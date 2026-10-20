"""Auditor-authored, append-only local assessment guidance."""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404,JsonResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.views.decorators.http import require_http_methods
from .assessment_config import current_question
from .models import Assessment, Requirement, Response, Site, SiteQuestionVersion
from .views import site_access,log


class SiteQuestionForm(forms.Form):
    kind=forms.ChoiceField(choices=[('local_guidance','Local wording/evidence guidance'),('official_proposal','Proposal to change an official obligation')])
    question_text=forms.CharField(widget=forms.Textarea(attrs={'rows':4}),label='Site question or proposed wording')
    evidence_items=forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':5}),label='Evidence needs (one per line)')
    local_explanation=forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':3}),label='Local explanation')
    change_reason=forms.CharField(widget=forms.Textarea(attrs={'rows':2}),label='Reason for change')
    expected_version=forms.IntegerField(min_value=0,widget=forms.HiddenInput)


@login_required
def configuration(request,site_code):
    site=site_access(request,site_code)
    query=request.GET.get('q','').strip()
    from .catalogue import working_requirements
    reqs=working_requirements(site).select_related('category')
    if query: reqs=reqs.filter(Q(code__icontains=query)|Q(detail_text__icontains=query)|Q(expected_evidence__icontains=query))
    page=Paginator(reqs,25).get_page(request.GET.get('page'))
    latest={v.requirement_id:v for v in SiteQuestionVersion.objects.filter(site=site,kind='local_guidance').order_by('version')}
    for req in page.object_list: req.local_version=latest.get(req.code)
    can_edit=site.membership_set.filter(user=request.user,role='assessor').exists()
    approved=Assessment.objects.filter(site=site,status='approved').first()
    prior_advisories=[]
    if approved:
        from .access import allowed_classifications
        from .models import Evidence
        visible_ids=set(Evidence.objects.filter(site=site,classification__in=allowed_classifications(request.user,site)).values_list('pk',flat=True))
        for response in Response.objects.filter(assessment=approved,code='A').select_related('requirement'):
            clause_ids=list(response.requirement.clauses.values_list('id',flat=True))
            evidence=[row['evidence_title'] for row in approved.snapshot.get('coverage',[])
                if row['clause_id'] in clause_ids and row.get('evidence_id') in visible_ids]
            prior_advisories.append({'response':response,'evidence':list(dict.fromkeys(evidence))})
    return render(request,'assessment_configuration.html',{'site':site,'page':page,'query':query,
        'can_edit':can_edit,'latest_assessment':site.assessments.first(),'prior_advisories':prior_advisories})


@login_required
@require_http_methods(['GET','POST'])
def question_configuration(request,site_code,req_code):
    site=site_access(request,site_code)
    from .catalogue import working_requirements
    req=get_object_or_404(working_requirements(site).prefetch_related('clauses'),code=req_code)
    history=list(SiteQuestionVersion.objects.filter(site=site,requirement=req).select_related('author'))
    current=current_question(site,req)
    latest=history[0].version if history else 0
    can_edit=site.membership_set.filter(user=request.user,role='assessor').exists()
    if request.method=='POST':
        site_access(request,site_code,['assessor'])
        form=SiteQuestionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                Site.objects.select_for_update().get(pk=site.pk)
                last=SiteQuestionVersion.objects.filter(site=site,requirement=req).first()
                version=last.version if last else 0
                if version!=form.cleaned_data['expected_version']:
                    return JsonResponse({'error':'Site wording changed. Reload and compare versions before saving.'},status=409)
                fields={'question_text':form.cleaned_data['question_text'],
                        'evidence_items':[line.strip() for line in form.cleaned_data['evidence_items'].splitlines() if line.strip()],
                        'local_explanation':form.cleaned_data['local_explanation']}
                diff={key:{'before':current.get(key),'after':value} for key,value in fields.items() if current.get(key)!=value}
                if not diff: form.add_error(None,'No wording, evidence or explanation changed.')
                else:
                    row=SiteQuestionVersion.objects.create(site=site,requirement=req,version=version+1,
                        kind=form.cleaned_data['kind'],change_reason=form.cleaned_data['change_reason'],
                        diff=diff,author=request.user,**fields)
                    log(site,request.user,'site_question_version_created',row,{'requirement':req.code,'kind':row.kind,'version':row.version})
                    messages.success(request,'Local guidance version saved.' if row.kind=='local_guidance' else 'Official change proposal retained; it is not effective without governed approval.')
                    return redirect('question_configuration',site_code=site.code,req_code=req.code)
    else:
        form=SiteQuestionForm(initial={'kind':'local_guidance','question_text':current['question_text'],
            'evidence_items':'\n'.join(current['evidence_items']),'local_explanation':current['local_explanation'],'expected_version':latest})
    return render(request,'question_configuration.html',{'site':site,'req':req,'current':current,'history':history,
        'form':form,'can_edit':can_edit})
