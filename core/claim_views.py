"""Participant claims and reasoned, targeted assessment decisions."""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max,Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from .models import *
from .views import site_access,log
from .access import allowed_classifications
from .readiness import assessment_snapshot
from .progress import scope_for

class ClaimForm(forms.Form):
    requirement=forms.ModelChoiceField(queryset=Requirement.objects.all())
    statement=forms.CharField(widget=forms.Textarea(attrs={'rows':3}),label='Readiness statement / evidence conclusion')
    evidence=forms.ModelMultipleChoiceField(queryset=Evidence.objects.none(),widget=forms.SelectMultiple(attrs={'size':5}))
    event=forms.ModelChoiceField(queryset=Kaizen.objects.none(),required=False)

class DecisionForm(forms.Form):
    decision=forms.ChoiceField(choices=[('accepted','Accept verified requirement'),('returned','Return for further work')])
    reason=forms.CharField(widget=forms.Textarea(attrs={'rows':3}))
    revision=forms.IntegerField(widget=forms.HiddenInput)

@login_required
def claims(request,site_code):
    site=site_access(request,site_code)
    form=ClaimForm(request.POST or None)
    form.fields['evidence'].queryset=Evidence.objects.filter(site=site,classification__in=allowed_classifications(request.user,site))
    form.fields['event'].queryset=Kaizen.objects.filter(site=site)
    current=site.assessments.first();scope=scope_for(current)
    form.fields['requirement'].queryset=Requirement.objects.filter(code__in=scope.get('requirements',[]))
    if request.method=='POST':
        site_access(request,site_code,['staff','assessor','coach','manager','admin'])
        if form.is_valid():
            with transaction.atomic():
                Site.objects.select_for_update().get(pk=site.pk)
                claim=VerificationClaim.objects.create(site=site,requirement=form.cleaned_data['requirement'],event=form.cleaned_data['event'],statement=form.cleaned_data['statement'],created_by=request.user)
                claim.evidence.set(form.cleaned_data['evidence']);log(site,request.user,'requirement_ready_for_verification',claim)
            messages.success(request,'Ready for verification recorded. Verified coverage and Y are unchanged.')
            return redirect('claims',site_code=site.code)
    review=Membership.objects.filter(user=request.user,site=site,role__in=['assessor','manager','admin']).exists()
    return render(request,'claims.html',{'site':site,'form':form,'claims':VerificationClaim.objects.filter(site=site).select_related('requirement','event').order_by('-created_at'),'can_review':review})

@login_required
def claim_review(request,site_code,pk):
    site=site_access(request,site_code,['assessor','manager','admin']);claim=get_object_or_404(VerificationClaim,site=site,pk=pk)
    form=DecisionForm(request.POST or None,initial={'revision':claim.revision})
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            Site.objects.select_for_update().get(pk=site.pk)
            claim=VerificationClaim.objects.select_for_update().get(pk=pk)
            if claim.status!='pending' or claim.revision!=form.cleaned_data['revision']: return JsonResponse({'error':'Claim already changed. Reload the decision.'},status=409)
            evidence=claim.evidence.filter(site=site,classification__in=allowed_classifications(request.user,site))
            if form.cleaned_data['decision']=='accepted':
                covered=set(Coverage.objects.filter(evidence__in=evidence,accepted=True,reviewed_by__isnull=False,reviewed_at__isnull=False)
                            .filter(~Q(evidence__evidence_type='audit')|Q(evidence__other_audit__isnull=False))
                            .filter(Q(evidence__valid_until__isnull=True)|Q(evidence__valid_until__gte=timezone.localdate())).values_list('clause_id',flat=True))
                required=set(claim.requirement.clauses.values_list('pk',flat=True))
                latest=site.assessments.first();scope=scope_for(latest)
                if not required or not required.issubset(covered): form.add_error(None,'Every detail clause needs current accepted coverage in the linked claim evidence. Review clause coverage first.')
                elif not scope.get('known') or claim.requirement_id not in scope.get('requirements',[]): form.add_error(None,'Requirement is not in a known frozen scope. Resolve the configuration before accepting.')
                elif site.assessments.filter(status='draft').exists(): form.add_error(None,'An assessment draft is open. Complete or approve that draft first; targeted decisions must not displace ongoing assessment work.')
                if not form.errors:
                    version=(site.assessments.aggregate(v=Max('version'))['v'] or 0)+1
                    assessment=Assessment.objects.create(site=site,version=version,created_by=request.user,scope_snapshot=scope,full_section_review=False,rationale='Targeted requirement review: '+form.cleaned_data['reason'])
                    if latest:
                        Response.objects.bulk_create([Response(assessment=assessment,requirement_id=r.requirement_id,code=r.code,conclusion=r.conclusion,updated_by_id=r.updated_by_id) for r in latest.responses.all() if r.requirement_id!=claim.requirement_id])
                    Response.objects.create(assessment=assessment,requirement=claim.requirement,code='Y',conclusion=form.cleaned_data['reason'],updated_by=request.user)
                    assessment.status='approved';assessment.approved_by=request.user;assessment.approved_at=timezone.now();assessment.snapshot=assessment_snapshot(site,assessment);assessment.save()
                    claim.assessment=assessment
            if not form.errors:
                claim.status=form.cleaned_data['decision'];claim.decision=form.cleaned_data['reason'];claim.reviewed_by=request.user;claim.reviewed_at=timezone.now();claim.revision+=1;claim.save()
                log(site,request.user,'targeted_requirement_'+claim.status,claim,{'assessment':claim.assessment_id,'full_section_review':False})
                messages.success(request,'Requirement decision recorded as a targeted review; full-section assessment frequency was not reset.')
                return redirect('claims',site_code=site.code)
    return render(request,'claim_review.html',{'site':site,'claim':claim,'form':form,'evidence':claim.evidence.filter(classification__in=allowed_classifications(request.user,site))})
