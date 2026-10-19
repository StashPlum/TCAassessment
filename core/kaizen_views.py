"""Stage 4 routes: task progress, sensei review decisions and A3/A4 PDF + XLSX downloads.

Every route re-checks site membership and event-team rights on the server. Finalising a Kaizen
never changes a TCA response.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .access import can_edit_event, report_visible
from .forms import ReviewDecisionForm
from .kaizen import (REVIEW_KEYS, REVIEW_STATE_LABELS, changed_since_review, checkpoint, gate_summary, pdca_segments,
                     reopen_after_change, review_checks, review_state, team_display, initials)
from .measurements import compare_observations
from .models import Kaizen, KaizenAction, Membership, ReviewNote
from .views import _with_bars, log, site_access

SENSEI=['coach','manager','admin']

@login_required
@require_POST
def task_progress(request,site_code,pk,action_pk):
    site=site_access(request,site_code,['staff','coach','manager','admin'])
    with transaction.atomic():
        event=get_object_or_404(Kaizen.objects.select_for_update(),site=site,pk=pk)
        action=get_object_or_404(KaizenAction,event=event,pk=action_pk)
        assignee=action.assignee_id and action.assignee.user_id==request.user.pk
        if not (assignee or can_edit_event(request.user,event)): raise Http404
        value=request.POST.get('progress','')
        if not value.isdigit() or int(value)>100: return JsonResponse({'message':'Progress is a whole number from 0 to 100.'},status=422)
        if request.POST.get('event_revision')!=str(event.revision):
            if request.headers.get('X-Requested-With')=='XMLHttpRequest':
                return JsonResponse({'message':'Another edit was saved. Reload before changing progress.'},status=409)
            messages.error(request,'Another edit was saved. Reload before changing progress; nothing was overwritten.')
        else:
            checkpoint(event,request.user,'Before task progress')
            action.progress=int(value);action.save(update_fields=['progress'])
            reopen_after_change(event);event.revision+=1;event.save();checkpoint(event,request.user,'Task progress updated')
            log(site,request.user,'kaizen_task_progress',action,{'progress':action.progress})
            if request.headers.get('X-Requested-With')=='XMLHttpRequest': return JsonResponse({'revision':event.revision,'progress':action.progress})
            messages.success(request,f'Progress saved: {action.progress}%.')
    target=request.POST.get('next','')
    if target=='home': return redirect('home')
    view='&view=gantt' if request.POST.get('actions_view')=='gantt' else ''
    return redirect(reverse('kaizen_detail',args=[site.code,pk])+'?stage='+request.POST.get('workspace_stage','Do')+view)

def _review_context(request,site,event,form):
    previous,changes=changed_since_review(event)
    return {'site':site,'event':event,'form':form,'gates':gate_summary(event),'missing':review_checks(event),
            'state':review_state(event),'state_label':REVIEW_STATE_LABELS[review_state(event)],'segments':pdca_segments(event),
            'previous_review':previous,'review_changes':changes,'comparisons':_with_bars(compare_observations(event.observations.all())),
            'open_requests':event.review_notes.filter(kind__in=['return','clarify'],resolved=False).select_related('actor'),
            'notes':event.review_notes.select_related('actor').order_by('-created_at')[:30],
            'team':[{'name':team_display(p),'initials':initials(team_display(p)),'role':p.kaizen_role} for p in event.participants.select_related('user')],
            'actions':event.actions.select_related('assignee__user').order_by('start_date','pk'),
            'reports':[r for r in event.a3_reports.order_by('-version') if report_visible(r,request.user)]}

@login_required
def review_detail(request,site_code,pk):
    """Sensei review: changes, gates, before/after, feedback per phase, return or finalise."""
    site=site_access(request,site_code,SENSEI)
    event=get_object_or_404(Kaizen,site=site,pk=pk)
    form=ReviewDecisionForm(request.POST or None,initial={'revision':event.revision,'coach_review':event.data.get('coach_review','')})
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            event=Kaizen.objects.select_for_update().get(pk=event.pk)
            if form.cleaned_data['revision']!=event.revision:
                form.add_error(None,'The team saved a newer revision. Your feedback is kept here; review the changes before deciding.')
            elif form.cleaned_data['decision']=='return':
                checkpoint(event,request.user,'Before sensei return')
                for phase,text in form.comments():
                    ReviewNote.objects.create(event=event,stage=phase,kind='return',text=text,actor=request.user,event_revision=event.revision)
                if form.cleaned_data['coach_review'].strip(): event.data={**event.data,'coach_review':form.cleaned_data['coach_review'].strip()}
                event.status='in_progress';event.revision+=1;event.save();checkpoint(event,request.user,'Returned with sensei feedback')
                log(site,request.user,'kaizen_returned',event,{'phases':[p for p,_ in form.comments()]})
                messages.success(request,'Returned to the team with feedback per phase. The team sees it in the PDCA workspace.')
                return redirect('review_queue',site_code=site.code)
            else:
                if form.cleaned_data['coach_review'].strip(): event.data={**event.data,'coach_review':form.cleaned_data['coach_review'].strip()}
                missing=review_checks(event)
                if event.status!='results_under_review': form.add_error(None,'Only an event submitted for review can be finalised.')
                elif missing: form.add_error(None,'Finalising needs every gate: '+', '.join(missing))
                else:
                    checkpoint(event,request.user,'Before sensei finalisation')
                    for phase,text in form.comments():
                        ReviewNote.objects.create(event=event,stage=phase,kind='advice',text=text,actor=request.user,event_revision=event.revision)
                    event.status='verified';event.revision+=1;event.save();checkpoint(event,request.user,'Finalised by sensei')
                    from .a3 import ensure_reports
                    ensure_reports(event,request.user)
                    log(site,request.user,'kaizen_finalised',event,{'revision':event.revision})
                    messages.success(request,'Finalised. A3 and A4 PDF versions are stored for this revision. Linked TCA answers were not changed.')
                    return redirect('kaizen_review_detail',site_code=site.code,pk=event.pk)
                if form.errors: event.refresh_from_db()
    return render(request,'review_detail.html',_review_context(request,site,event,form))

# ---------- downloads ----------

def _event_or_404(request,site_code,pk):
    site=site_access(request,site_code)
    return site,get_object_or_404(Kaizen,site=site,pk=pk)

@login_required
def event_export(request,site_code,pk,fmt):
    """A3/A4 PDF or report XLSX of one event; stored finalised versions win over working copies."""
    from .a3 import RENDERER_VERSION,working_pdf
    from .report_exports import events_xlsx
    site,event=_event_or_404(request,site_code,pk)
    if fmt=='pdf':
        paper=request.GET.get('paper','A3')
        if paper not in ('A3','A4'): raise Http404
        stored=event.a3_reports.filter(event_revision=event.revision,paper=paper,renderer_version=RENDERER_VERSION).order_by('-version').first()
        if stored and report_visible(stored,request.user):
            with stored.file.open('rb') as handle: raw=handle.read()
            name=f'KZ-{event.pk}-{paper}-v{stored.version}.pdf'
        else:
            raw=working_pdf(event,paper);name=f'KZ-{event.pk}-{paper}-r{event.revision}-working-copy.pdf'
        response=HttpResponse(raw,content_type='application/pdf')
    elif fmt=='xlsx':
        response=HttpResponse(events_xlsx([event],request.user).getvalue(),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        name=f'KZ-{event.pk}-r{event.revision}.xlsx'
    else: raise Http404
    response['Content-Disposition']=f'attachment; filename="{name}"';response['Cache-Control']='private, no-store'
    log(site,request.user,'kaizen_exported',event,{'format':fmt,'paper':request.GET.get('paper','')})
    return response

@login_required
def review_export(request,site_code,fmt):
    """One or selected queue events; only events of this site are ever included."""
    from .report_exports import events_pdf,events_xlsx
    site=site_access(request,site_code,SENSEI)
    ids=[int(x) for x in request.GET.getlist('ids') if x.isdigit()]
    events=list(Kaizen.objects.filter(site=site,pk__in=ids).order_by('-submitted_at','-updated_at'))
    if not ids or len(events)!=len(set(ids)): raise Http404
    if fmt=='xlsx':
        response=HttpResponse(events_xlsx(events,request.user).getvalue(),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        name=f'sensei-review-{len(events)}-events.xlsx'
    elif fmt=='pdf':
        paper=request.GET.get('paper','A3')
        if paper not in ('A3','A4'): raise Http404
        response=HttpResponse(events_pdf(events,request.user,paper),content_type='application/pdf');name=f'sensei-review-{len(events)}-events-{paper}.pdf'
    else: raise Http404
    response['Content-Disposition']=f'attachment; filename="{name}"';response['Cache-Control']='private, no-store'
    log(site,request.user,'review_queue_exported',events[0],{'format':fmt,'events':ids})
    return response

@login_required
def toolbox_library(request,site_code):
    """Site-level Lean toolbox: browse every method and its help without an event."""
    from .toolbox_registry import REGISTRY
    site=site_access(request,site_code)
    stage=request.GET.get('stage','');kind=request.GET.get('kind','');q=request.GET.get('q','').strip()[:100]
    specs=list(REGISTRY.values())
    counts={s:sum(spec['stage']==s for spec in specs) for s in ('Plan','Do','Check','Act')}
    kinds=sorted({spec['kind'] for spec in specs})
    if stage not in counts: stage=''
    if kind not in kinds: kind=''
    shown=[spec for spec in specs if (not stage or spec['stage']==stage) and (not kind or spec['kind']==kind)
           and q.casefold() in (spec['name']+' '+spec['purpose']).casefold()]
    selected=REGISTRY.get(request.GET.get('method','')) or (shown[0] if shown else None)
    query=request.GET.copy();query.pop('method',None)
    return render(request,'toolbox_library.html',{'site':site,'specs':shown,'total':len(specs),'selected':selected,'stage':stage,'kind':kind,'kinds':kinds,
        'query':q,'counts':counts,'filter_query':query.urlencode(),'filters_active':bool(stage or kind or q)})
