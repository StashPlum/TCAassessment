import json,zipfile
from copy import deepcopy
from io import BytesIO
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse,HttpResponse,Http404,JsonResponse
from django.shortcuts import get_object_or_404,render,redirect
from django.views.decorators.http import require_POST
from .models import *
from .views import site_access,log
from .context import authorized_sites
from .a3 import report_snapshot,summary_sections,ensure_report
from .kaizen import checkpoint,public_snapshot,snapshot,PROTECTED_STATES
from .access import visible_attachments,allowed_classifications,report_visible
from .toolbox_registry import REGISTRY
from .toolbox_visuals import render_svg
from .toolbox_views import worksheet_checkpoint

@login_required
def a3_preview(request,site_code,pk):
    site=site_access(request,site_code);event=get_object_or_404(Kaizen,site=site,pk=pk);content=report_snapshot(event)
    reports=[report for report in event.a3_reports.all().order_by('-version') if report_visible(report,request.user)]
    return render(request,'a3_preview.html',{'site':site,'event':event,'sections':summary_sections(content),'reports':reports,
        'worksheets':[(w,render_svg(w.method,w.payload)) for w in event.worksheets.filter(include_in_a3=True) if w.method in REGISTRY],
        'can_publish':site.membership_set.filter(user=request.user,role__in=['manager','admin']).exists()})

@login_required
def a3_download(request,site_code,pk,report_pk):
    site=site_access(request,site_code);event=get_object_or_404(Kaizen,site=site,pk=pk);report=get_object_or_404(A3Report,event=event,pk=report_pk)
    if not report_visible(report,request.user):raise Http404
    response=FileResponse(report.file.open('rb'),as_attachment=True,filename=f'kaizen-{pk}-a3-v{report.version}.pdf');response['Cache-Control']='private, no-store';return response

@login_required
@require_POST
def a3_finalize(request,site_code,pk):
    site=site_access(request,site_code,['staff','coach','manager','admin'])
    with transaction.atomic():
        event=get_object_or_404(Kaizen.objects.select_for_update(),site=site,pk=pk)
        if str(event.revision)!=request.POST.get('revision'):return JsonResponse({'error':'Event changed. Reload before finalizing a report.'},status=409)
        if event.local_status!='closed' and event.status not in PROTECTED_STATES:return JsonResponse({'error':'Close the local PDCA or complete the existing global review first.'},status=422)
        report=ensure_report(event,request.user);log(site,request.user,'a3_report_finalized',report,{'event_revision':event.revision})
    return redirect('a3_preview',site_code=site.code,pk=pk)

@login_required
def event_archive_zip(request,site_code,pk):
    site=site_access(request,site_code);event=get_object_or_404(Kaizen,site=site,pk=pk)
    roles=set(Membership.objects.filter(user=request.user,site=site).values_list('role',flat=True))
    financial=bool(roles&{'assessor','manager','admin'});participants=bool(roles&{'assessor','coach','manager','admin'})
    content=public_snapshot(snapshot(event),financial,participants)
    content['history']=[{'revision':r.revision,'state':r.state,'snapshot':public_snapshot(r.snapshot,financial,participants)} for r in event.history.all()]
    output=BytesIO()
    from django.core.serializers.json import DjangoJSONEncoder
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('event-complete.json',json.dumps(content,cls=DjangoJSONEncoder,ensure_ascii=False,indent=2))
        for worksheet in event.worksheets.all():
            if worksheet.method in REGISTRY: archive.writestr(f'worksheets/{worksheet.pk}-r{worksheet.revision}.svg',render_svg(worksheet.method,worksheet.payload))
        for item in visible_attachments(event,request.user):
            if item.file:
                with item.file.open('rb') as file:archive.writestr(f'originals/attachment-{item.pk}-{item.original_name}',file.read())
            elif item.evidence and item.evidence.file and item.evidence.classification in allowed_classifications(request.user,site) and item.evidence.site_id==site.pk:
                from pathlib import Path
                with item.evidence.file.open('rb') as file:archive.writestr(f'originals/evidence-{item.evidence_id}-{Path(item.evidence.file.name).name}',file.read())
        for report in event.a3_reports.all():
            if not report_visible(report,request.user):continue
            with report.file.open('rb') as file:archive.writestr(f'reports/a3-v{report.version}.pdf',file.read())
    response=HttpResponse(output.getvalue(),content_type='application/zip');response['Content-Disposition']=f'attachment; filename="kaizen-{pk}-complete.zip"';return response

class SharingForm(forms.Form):
    context=forms.CharField(widget=forms.Textarea(attrs={'rows':3}),label='Local context and demonstrated learning')
    transfer_limits=forms.CharField(widget=forms.Textarea(attrs={'rows':3}),label='Transfer limitations / checks needed at another site')
    allowed_sites=forms.ModelMultipleChoiceField(queryset=Site.objects.none(),widget=forms.SelectMultiple(attrs={'size':5}),label='Explicit authorized sharing scope (local pilot sites)')
    approval_reason=forms.CharField(widget=forms.Textarea(attrs={'rows':2}),label='Sharing approval reason')
    revision=forms.IntegerField(widget=forms.HiddenInput)

def learning_approach(event):
    """Copy methods/hypotheses only; strip people, amounts, proofs and reviews."""
    fields=('overall_problem','specific_problem','root_cause','solution','sustain','outcome_criterion')
    tools=[]
    for w in event.worksheets.filter(include_in_a3=True):
        if w.method not in REGISTRY: continue
        # Learning copies schema and procedure, not measured datasets or scored results.
        tools.append({'method':w.method,'schema_version':w.schema_version,'stage':w.stage,'title':w.title,
                      'learning':w.payload.get('conclusion','')})
    return {'data':{k:event.data.get(k,'') for k in fields},'methods':tools,'policy':'Approach only; no evidence, observations, savings, team, reviews or requirement Y inherited.'}

@login_required
def learning_publish(request,site_code,pk):
    site=site_access(request,site_code,['manager','admin']);event=get_object_or_404(Kaizen,site=site,pk=pk)
    form=SharingForm(request.POST or None,initial={'revision':event.revision})
    # A publisher needs membership in every destination; no implicit all-site sharing.
    form.fields['allowed_sites'].queryset=authorized_sites(request.user)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            event=Kaizen.objects.select_for_update().get(pk=pk)
            if event.revision!=form.cleaned_data['revision']: form.add_error(None,'Event changed. Review the current learning and sharing scope first.')
            elif event.status not in PROTECTED_STATES: form.add_error(None,'Existing sensei verification is required before publishing learning; local closure alone is insufficient.')
            elif not event.a3_reports.filter(event_revision=event.revision).exists():form.add_error(None,'Finalize a report at the current reviewed revision first.')
            if not form.errors:
                report=event.a3_reports.filter(event_revision=event.revision).order_by('-version').first()
                entry=LearningEntry.objects.create(event=event,report=report,title=event.title,context=form.cleaned_data['context'],transfer_limits=form.cleaned_data['transfer_limits'],approach=learning_approach(event),approved_by=request.user,approval_reason=form.cleaned_data['approval_reason'])
                entry.allowed_sites.set(form.cleaned_data['allowed_sites']);log(site,request.user,'learning_shared_local_scope',entry,{'site_ids':list(entry.allowed_sites.values_list('pk',flat=True))})
                messages.success(request,'Learning shared only with the explicitly selected local pilot sites. Corporate publication authority remains pending.')
                return redirect('learning',site_code=site.code)
    return render(request,'learning_publish.html',{'site':site,'event':event,'form':form})

@login_required
def learning(request,site_code):
    site=site_access(request,site_code);q=request.GET.get('q','').strip()
    items=LearningEntry.objects.filter(allowed_sites=site).select_related('event__site','report').order_by('-created_at')
    if q:items=items.filter(title__icontains=q)
    return render(request,'learning.html',{'site':site,'items':items,'query':q})

@login_required
@require_POST
def learning_adapt(request,site_code,pk):
    site=site_access(request,site_code,['staff','coach','manager','admin'])
    entry=get_object_or_404(LearningEntry,pk=pk,allowed_sites=site)
    title=request.POST.get('title','').strip()
    if not title or len(title)>200:return JsonResponse({'error':'Supply a local title, at most 200 characters.'},status=422)
    with transaction.atomic():
        event=Kaizen.objects.create(site=site,title=title,profile='A4',input_profile='medium',created_by=request.user,
            data={'overall_problem':title,'owner':request.user.username,'process_location':site.name,
                  'adapted_from_learning':entry.pk,'transfer_limits':entry.transfer_limits,
                  'approach_reference':deepcopy(entry.approach),'root_cause':'Hypothesis from prior approach; local validation required.'})
        from .toolbox_registry import initial_payload
        for tool in entry.approach.get('methods',[]):
            payload=initial_payload(tool['method'],event);payload['learning_reference']=tool['learning']
            w=Worksheet.objects.create(event=event,method=tool['method'],stage=tool['stage'],title=tool['title'],schema_version=REGISTRY[tool['method']]['version'],payload=payload);worksheet_checkpoint(w,request.user)
        checkpoint(event,request.user,'Adapted approach only; all local review/results reset');log(site,request.user,'learning_approach_adapted',event,{'learning':entry.pk})
    return redirect('kaizen_detail',site_code=site.code,pk=event.pk)
