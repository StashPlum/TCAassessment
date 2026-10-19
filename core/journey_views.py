"""Stage-three preparation, scheduling and dated history around the existing assessment domain."""
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .assessment_config import current_preparation, current_question
from .assessment_documents import assessment_records, pdf_bytes, preparation_records, xlsx_bytes
from .forms import PreparationNeedForm, PreparationFilterForm, SessionChangeForm, SessionReviewForm
from .models import Assessment, AssessmentSession, Coverage, PreparationNeedVersion, Requirement, SessionRevision, Site
from .preparation_service import preparation_items
from .views import log, site_access
from .context import authorized_sites
from .access import allowed_classifications


def _download(content, filename, fmt):
    mime='application/pdf' if fmt=='pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response=HttpResponse(content,content_type=mime)
    response['Content-Disposition']=f'attachment; filename="{filename}.{fmt}"'
    response['Cache-Control']='private, no-store'
    return response


@login_required
def preparation_need(request,site_code,req_code):
    site=site_access(request,site_code)
    req=get_object_or_404(Requirement.objects.select_related('category').prefetch_related('clauses'),code=req_code)
    history=list(PreparationNeedVersion.objects.filter(site=site,requirement=req).select_related('author'))
    current=current_preparation(site,req)
    can_edit=site.membership_set.filter(user=request.user,role='assessor').exists()
    if request.method=='POST':
        site_access(request,site_code,['assessor'])
        form=PreparationNeedForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                Site.objects.select_for_update().get(pk=site.pk)
                latest=PreparationNeedVersion.objects.filter(site=site,requirement=req).first()
                version=latest.version if latest else 0
                if version!=form.cleaned_data['expected_version']:
                    return JsonResponse({'error':'Documentation needs changed. Reload and compare versions.'},status=409)
                fields={'evidence_items':[line.strip() for line in form.cleaned_data['evidence_items'].splitlines() if line.strip()],
                    'owner':form.cleaned_data['owner'],
                    'period_start':form.cleaned_data['period_start'],
                    'period_end':form.cleaned_data['period_end'],
                    'source_note':form.cleaned_data['source_note']}
                diff={key:{'before':current[key],'after':value.isoformat() if isinstance(value,date) else value}
                    for key,value in fields.items() if current[key]!=(value.isoformat() if isinstance(value,date) else value)}
                if not diff:form.add_error(None,'No documentation need changed.')
                else:
                    row=PreparationNeedVersion.objects.create(site=site,requirement=req,version=version+1,
                        change_reason=form.cleaned_data['change_reason'],diff=diff,author=request.user,**fields)
                    log(site,request.user,'preparation_need_version_created',row,{'requirement':req.code,'version':row.version})
                    messages.success(request,'Site documentation need version saved for future assessments.')
                    return redirect('preparation_need',site_code=site.code,req_code=req.code)
    else:
        form=PreparationNeedForm(initial={'evidence_items':'\n'.join(current['evidence_items']),
            'owner':current['owner'],'period_start':current['period_start'],'period_end':current['period_end'],
            'source_note':current['source_note'],'expected_version':current['version']})
    return render(request,'preparation_need.html',{'site':site,'req':req,'current':current,
        'question':current_question(site,req),'history':history,'form':form,'can_edit':can_edit})


@login_required
def preparation_export(request,site_code,fmt):
    site=site_access(request,site_code)
    if fmt not in ('xlsx','pdf'):raise Http404
    scope=request.GET.get('scope','filtered')
    if scope not in ('filtered','selected'):raise Http404
    if scope=='selected':
        selected=request.session.get('preparation_selected',{}).get(site.code,[])
        if not selected:return HttpResponse('No requirements selected for export.',status=400)
        items=preparation_items(site,{},selected=selected)
        label=f'Selected requirements across pages ({len(items)})'
    else:
        filters=PreparationFilterForm(request.session.get('preparation_filters',{}).get(site.code,{}))
        if not filters.is_valid():return HttpResponse('Invalid preparation filters.',status=400)
        items=preparation_items(site,filters.cleaned_data)
        applied=', '.join(f'{key}={value}' for key,value in filters.cleaned_data.items() if value)
        label=f'All matching current filters ({len(items)}): {applied or "none"}'
    records=preparation_records(site,items)
    title=f'{site.organization} | TCA evidence preparation | {site.name}'
    content=pdf_bytes(title,records,label) if fmt=='pdf' else xlsx_bytes(title,records,label)
    return _download(content,f'preparation-{site.code}',fmt)


def _session_state(session):
    return {'date':session.date.isoformat(),'method':session.method,'purpose':session.purpose,
        'scope_text':session.scope_text,'participants':session.participants,'time_blocks':session.time_blocks,
        'notes':session.notes,'owner':session.owner,'requirements':list(session.requirements.values_list('code',flat=True)),
        'availability':session.availability,'alternate_date':session.alternate_date.isoformat() if session.alternate_date else '',
        'backup_participants':session.backup_participants,'manager_note':session.manager_note}


def _blocks_text(session):
    return '\n'.join(f"{row['start']}-{row['end']} | {row['people']} | {row['role']}" for row in session.time_blocks)


@login_required
def session_detail(request,site_code,pk):
    site=site_access(request,site_code)
    session=get_object_or_404(AssessmentSession.objects.prefetch_related('requirements','history__actor'),site=site,pk=pk)
    can_plan=site.membership_set.filter(user=request.user,role__in=['assessor','manager','admin']).exists()
    can_review=site.membership_set.filter(user=request.user,role__in=['manager','admin']).exists()
    change_form=SessionChangeForm(initial={**_session_state(session),'blocks_text':_blocks_text(session),
        'revision':session.revision}) if can_plan else None
    review_form=SessionReviewForm(initial={'availability':session.availability if session.availability!='proposed' else 'confirmed',
        'alternate_date':session.alternate_date,'backup_participants':session.backup_participants,
        'manager_note':session.manager_note,'revision':session.revision}) if can_review else None
    if request.method=='POST':
        site_access(request,site_code,['assessor','manager','admin'])
        action=request.POST.get('action')
        if action=='change':change_form=SessionChangeForm(request.POST,instance=session)
        elif action=='review':
            site_access(request,site_code,['manager','admin'])
            review_form=SessionReviewForm(request.POST)
        else:raise Http404
        form=change_form if action=='change' else review_form
        if action=='review' and form.is_valid() and form.cleaned_data['availability']=='confirmed' and not session.time_blocks:
            form.add_error('availability','Add expected people and a time block before confirming availability.')
        if form.is_valid():
            with transaction.atomic():
                session=AssessmentSession.objects.select_for_update().get(pk=session.pk,site=site)
                if session.revision!=form.cleaned_data['revision']:
                    return JsonResponse({'error':'Plan changed. Reload and review before saving.'},status=409)
                before=_session_state(session)
                if action=='change':
                    changed=form.save(commit=False)
                    for field in ('date','method','purpose','scope_text','participants','notes','owner'):
                        setattr(session,field,getattr(changed,field))
                    session.time_blocks=form.cleaned_data['blocks_text']
                    session.availability='proposed';session.reviewed_by=None;session.reviewed_at=None
                    session.save();session.requirements.set(form.cleaned_data['requirements'])
                    reason=form.cleaned_data['change_reason'];impact=form.cleaned_data['impact']
                    followup=form.cleaned_data['followup_owner']
                else:
                    session.availability=form.cleaned_data['availability']
                    session.alternate_date=form.cleaned_data['alternate_date']
                    session.backup_participants=form.cleaned_data['backup_participants']
                    session.manager_note=form.cleaned_data['manager_note']
                    session.reviewed_by=request.user;session.reviewed_at=timezone.now();session.save()
                    reason='Manager availability review';impact=session.manager_note;followup=session.owner
                session.revision+=1;session.save(update_fields=['revision'])
                SessionRevision.objects.create(session=session,revision=session.revision,actor=request.user,
                    reason=reason,impact=impact,followup_owner=followup,before=before,after=_session_state(session))
                log(site,request.user,'assessment_session_changed',session,{'revision':session.revision,'action':action})
            messages.success(request,'Assessment plan updated. Participants can review the latest arrangement.')
            return redirect('session_detail',site_code=site.code,pk=session.pk)
    return render(request,'session_detail.html',{'site':site,'item':session,'change_form':change_form,
        'review_form':review_form,'can_plan':can_plan,'can_review':can_review})


@login_required
def assessment_history(request,site_code):
    site=site_access(request,site_code)
    sites=authorized_sites(request.user)
    chosen=request.GET.get('site',site.code)
    if chosen and not sites.filter(code=chosen).exists():raise Http404
    rows=Assessment.objects.filter(site__in=sites).select_related('site','created_by').order_by('-created_at','-pk')
    if chosen:rows=rows.filter(site__code=chosen)
    year=request.GET.get('year','');version=request.GET.get('version','');auditor=request.GET.get('auditor','')
    if year:
        if not year.isdigit() or len(year)!=4:raise Http404
        rows=rows.filter(created_at__year=int(year))
    if version:
        if not version.isdigit():raise Http404
        rows=rows.filter(version=int(version))
    if auditor:rows=rows.filter(created_by__username__icontains=auditor[:160])
    page=Paginator(rows,20).get_page(request.GET.get('page'))
    return render(request,'assessment_history.html',{'site':site,'sites':sites,'page':page,
        'chosen':chosen,'year':year,'version':version,'auditor':auditor,
        'active':bool(year or version or auditor or chosen!=site.code)})


@login_required
@require_POST
def assessment_history_export(request,site_code,fmt):
    site=site_access(request,site_code)
    if fmt not in ('xlsx','pdf'):raise Http404
    ids=request.POST.getlist('assessment_ids')
    if not ids or any(not value.isdigit() for value in ids):return HttpResponse('Select one or more assessments.',status=400)
    sites=authorized_sites(request.user)
    selected=list(Assessment.objects.filter(pk__in=ids,site__in=sites).select_related('site','created_by'))
    if len(selected)!=len(set(ids)):raise Http404
    selected.sort(key=lambda row:(row.site.name,row.version))
    records=[]
    for assessment in selected:
        records.extend(assessment_records(assessment,allowed_classifications(request.user,assessment.site)))
    label=', '.join(f'{row.site.name} v{row.version} ({row.status}, {row.policy_version})' for row in selected)
    title='CEVA Logistics | TCA assessment history'
    content=pdf_bytes(title,records,label) if fmt=='pdf' else xlsx_bytes(title,records,label)
    return _download(content,'assessment-history',fmt)
