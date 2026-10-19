"""Stage 5 libraries: learning repository, evidence library and reports/guidance.

All lists are built from records of the selected, authorized site (or learning explicitly shared
with it). Search results, downloads and CSV exports use the same queries as the pages.
"""
import csv
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .access import allowed_classifications
from .kaizen import REVIEW_STATE_LABELS, review_state
from .models import (Assessment, BestPracticeValidation, Category, Clause, Coverage, Evidence, EventAttachment, Kaizen,
                     LearningEntry, Membership, PreparationNeedVersion, Requirement, SiteQuestionVersion)
from .toolbox_registry import REGISTRY
from .views import log, site_access

def _csv(name,header,rows):
    response=HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition']=f'attachment; filename="{name}"'
    response.write('﻿')
    writer=csv.writer(response)
    safe=lambda v: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v
    writer.writerow(header)
    for row in rows: writer.writerow([safe(v) for v in row])
    return response

def _code(value):
    value=(value or '').strip().upper()
    return value if value and Requirement.objects.filter(code=value).exists() else ''

def _section(value):
    return value if value.isdigit() and Category.objects.filter(number=int(value)).exists() else ''

# ---------- learning ----------

def _learning_card(entry,user):
    event=entry.event
    snapshot=entry.report.snapshot if entry.report_id else {}
    comparison=next((c for c in snapshot.get('comparisons',[]) if c.get('before_average') is not None and c.get('after_average') is not None),None)
    if comparison:
        before=float(comparison['before_average']);after=float(comparison['after_average']);top=max(abs(before),abs(after)) or 1
        comparison={**comparison,'before':before,'after':after,'before_pct':round(abs(before)/top*100,1),'after_pct':round(abs(after)/top*100,1),
                    'delta':round(after-before,2),'delta_pct':round((after-before)/before*100) if before else None}
    data=entry.approach.get('data',{})
    can_open=Membership.objects.filter(user=user,site=event.site).exists()
    try: practice=entry.best_practice
    except BestPracticeValidation.DoesNotExist: practice=None
    return {'entry':entry,'codes':list(event.linked_requirements.values_list('code',flat=True)),'site':event.site,
            'problem':data.get('specific_problem') or data.get('overall_problem',''),'cause':data.get('root_cause',''),
            'approach':data.get('solution',''),'sustain':data.get('sustain',''),'methods':[m['title'] for m in entry.approach.get('methods',[])],
            'comparison':comparison,'event':event,'can_open_event':can_open,'practice':practice,
            'lineage':f'{event.get_profile_display()} · {event.get_input_profile_display()} · report r{entry.report.event_revision} (renderer v{entry.report.renderer_version})' if entry.report_id else event.get_profile_display()}

@login_required
def learning(request,site_code):
    site=site_access(request,site_code)
    req=_code(request.GET.get('req',''));section=_section(request.GET.get('section',''))
    method=request.GET.get('method','');q=request.GET.get('q','').strip()[:200];practice=request.GET.get('practice','')
    items=LearningEntry.objects.filter(allowed_sites=site).select_related('event__site','report').order_by('-created_at')
    if req: items=items.filter(event__linked_requirements__code=req)
    if section: items=items.filter(event__linked_requirements__category_id=int(section))
    if q: items=items.filter(Q(title__icontains=q)|Q(context__icontains=q))
    if practice=='validated': items=items.filter(best_practice__isnull=False)
    cards=[_learning_card(entry,request.user) for entry in items.distinct()]
    methods=sorted({title for card in [_learning_card(e,request.user) for e in LearningEntry.objects.filter(allowed_sites=site)] for title in card['methods']})
    if method in methods: cards=[c for c in cards if method in c['methods']]
    else: method=''
    selected=next((c for c in cards if str(c['entry'].pk)==request.GET.get('entry','')),cards[0] if cards else None)
    query=request.GET.copy();query.pop('entry',None)
    return render(request,'learning.html',{'site':site,'cards':cards,'selected':selected,'req':req,'section':section,'method':method,'methods':methods,
        'query':q,'practice':practice,'categories':Category.objects.all(),'filter_query':query.urlencode(),
        'filters_active':bool(req or section or method or q or practice),
        'can_validate':Membership.objects.filter(user=request.user,site=site,role='assessor').exists()})

@login_required
@require_POST
def best_practice_validate(request,site_code,pk):
    """Only a TCA auditor validates (user decision 19 Oct 2026); the record keeps who, when, how and what was checked."""
    site=site_access(request,site_code,['assessor'])
    entry=get_object_or_404(LearningEntry,pk=pk,allowed_sites=site)
    how=request.POST.get('how_achieved','').strip();basis=request.POST.get('validation_basis','').strip()
    target=reverse('learning',args=[site.code])+f'?entry={entry.pk}'
    if len(how)<10 or len(basis)<10:
        messages.error(request,'Describe how the result was achieved and what you checked (at least 10 characters each). Nothing was saved.')
        return redirect(target)
    with transaction.atomic():
        if BestPracticeValidation.objects.filter(entry=entry).exists():
            messages.info(request,'This learning is already validated as best practice; the earlier validation is kept.')
            return redirect(target)
        validation=BestPracticeValidation.objects.create(entry=entry,validated_by=request.user,how_achieved=how,validation_basis=basis)
        log(site,request.user,'best_practice_validated',validation,{'entry':entry.pk})
    messages.success(request,'Validated as best practice. Approver and date are shown on the card; TCA answers are unchanged.')
    return redirect(target)

# ---------- evidence library ----------

def evidence_status(item,today):
    if item.valid_until and item.valid_until<today: return 'expired'
    if any(c.accepted for c in item.coverage.all()): return 'accepted'
    return 'review'

EVIDENCE_STATUS={'accepted':'Accepted','review':'To review','expired':'Expired'}

def evidence_rows(request,site):
    today=timezone.localdate();g=request.GET
    filters={'req':_code(g.get('req','')),'section':_section(g.get('section','')),'type':g.get('type',''),'status':g.get('status',''),
             'owner':g.get('owner','').strip()[:160],'q':g.get('q','').strip()[:200],'from':g.get('from',''),'to':g.get('to','')}
    if filters['type'] not in dict(Evidence._meta.get_field('evidence_type').choices): filters['type']=''
    if filters['status'] not in EVIDENCE_STATUS: filters['status']=''
    for key in ('from','to'):
        try: filters[key]=date.fromisoformat(filters[key]) if filters[key] else ''
        except ValueError: filters[key]=''
    items=Evidence.objects.filter(site=site,classification__in=allowed_classifications(request.user,site)).prefetch_related('coverage__clause').order_by('-created_at')
    if filters['req']: items=items.filter(coverage__clause__requirement_id=filters['req'])
    if filters['section']: items=items.filter(coverage__clause__requirement__category_id=int(filters['section']))
    if filters['type']: items=items.filter(evidence_type=filters['type'])
    if filters['owner']: items=items.filter(owner__icontains=filters['owner'])
    if filters['q']: items=items.filter(Q(title__icontains=filters['q'])|Q(source__icontains=filters['q']))
    if filters['from']: items=items.filter(Q(period_end__gte=filters['from'])|Q(period_end__isnull=True,created_at__date__gte=filters['from']))
    if filters['to']: items=items.filter(Q(period_start__lte=filters['to'])|Q(period_start__isnull=True,created_at__date__lte=filters['to']))
    events={}
    for attachment in EventAttachment.objects.filter(evidence__site=site,event__site=site).select_related('event'):
        events.setdefault(attachment.evidence_id,{})[attachment.event_id]=attachment.event
    rows=[];counts={key:0 for key in EVIDENCE_STATUS}
    for item in items.distinct():
        status=evidence_status(item,today);counts[status]+=1
        if filters['status'] and status!=filters['status']: continue
        rows.append({'item':item,'status':status,'status_label':EVIDENCE_STATUS[status],
                     'codes':sorted({c.clause.requirement_id for c in item.coverage.all()}),'events':list(events.get(item.pk,{}).values())})
    return rows,counts,filters

@login_required
def evidence_library(request,site_code):
    from .forms import EvidenceForm
    if request.method=='POST':
        from .views import evidence as add_evidence
        return add_evidence(request,site_code)
    site=site_access(request,site_code)
    rows,counts,filters=evidence_rows(request,site)
    if request.GET.get('format')=='csv':
        return _csv(f'evidence-{site.code}.csv',['Evidence ID','Title','Type','Owner','Version','Period start','Period end','Valid until','Classification','Status','Requirements','Linked Kaizens','Created'],
            [[f'EV-{r["item"].pk}',r['item'].title,r['item'].get_evidence_type_display(),r['item'].owner,r['item'].version,r['item'].period_start,r['item'].period_end,
              r['item'].valid_until,r['item'].get_classification_display(),r['status_label'],' '.join(r['codes']),' '.join(f'KZ-{e.pk}' for e in r['events']),r['item'].created_at.date()] for r in rows])
    query=request.GET.copy();query.pop('status',None);query.pop('format',None)
    active=[(label,value) for label,value in [('Requirement',filters['req']),('Section',filters['section']),('Type',filters['type']),('Status',EVIDENCE_STATUS.get(filters['status'],'')),
            ('Owner',filters['owner']),('Search',filters['q']),('From',filters['from']),('To',filters['to'])] if value]
    return render(request,'evidence.html',{'site':site,'rows':rows,'counts':counts,'filters':filters,'active_filters':active,'base_query':query.urlencode(),
        'form':EvidenceForm(),'requested_requirement':filters['req'],'categories':Category.objects.all(),
        'types':Evidence._meta.get_field('evidence_type').choices,'statuses':EVIDENCE_STATUS,'requirement_codes':Requirement.objects.values_list('code',flat=True),
        'can_add':Membership.objects.filter(user=request.user,site=site,role__in=['assessor','coach','manager','admin']).exists(),
        'can_link':Membership.objects.filter(user=request.user,site=site,role__in=['assessor','manager','admin']).exists(),
        'can_review':Membership.objects.filter(user=request.user,site=site,role__in=['assessor','manager','admin']).exists(),
        'export_query':request.GET.urlencode()})

@login_required
@require_POST
def evidence_link_requirement(request,site_code,pk):
    """Reuse an existing evidence object for another requirement; never a second upload or duplicate link."""
    site=site_access(request,site_code,['assessor','manager','admin'])
    item=get_object_or_404(Evidence,site=site,pk=pk,classification__in=allowed_classifications(request.user,site))
    code=_code(request.POST.get('requirement_code',''))
    back=reverse('evidence',args=[site.code])+('?'+request.POST.get('back','') if request.POST.get('back') else '')
    if not code:
        messages.error(request,'Choose an existing TCA requirement ID.');return redirect(back)
    clauses=Clause.objects.filter(requirement_id=code)
    existing=set(Coverage.objects.filter(evidence=item,clause__in=clauses).values_list('clause_id',flat=True))
    new=[Coverage(evidence=item,clause=c) for c in clauses if c.pk not in existing]
    if not new:
        messages.info(request,f'EV-{item.pk} is already linked to {code}. No duplicate link or upload was created.');return redirect(back)
    Coverage.objects.bulk_create(new)
    log(site,request.user,'evidence_linked_requirement',item,{'requirement':code,'clauses':len(new)})
    messages.success(request,f'EV-{item.pk} linked to {code} ({len(new)} clause{"s" if len(new)!=1 else ""}, pending assessor review). The same file is reused.')
    return redirect(back)

# ---------- reports and guidance ----------

REPORT_TYPES=[('asm','Assessments'),('kz','Kaizens'),('guide','Guidance')]

def report_rows(request,site):
    g=request.GET;kind=g.get('type','asm')
    if kind not in dict(REPORT_TYPES): kind='asm'
    f={}
    if kind=='asm':
        items=Assessment.objects.filter(site=site).select_related('created_by','approved_by').order_by('-version')
        f['year']=g.get('year','') if g.get('year','').isdigit() else ''
        f['status']=g.get('status','') if g.get('status','') in ('draft','approved') else ''
        f['rule']=g.get('rule','') if g.get('rule','') in ('advisory-v2','draft-v1') else ''
        f['auditor']=g.get('auditor','').strip()[:150]
        f['advisory']=g.get('advisory','') if g.get('advisory','')=='open' else ''
        if f['year']: items=items.filter(created_at__year=int(f['year']))
        if f['status']: items=items.filter(status=f['status'])
        if f['rule']: items=items.filter(policy_version=f['rule'])
        if f['auditor']: items=items.filter(created_by__username__icontains=f['auditor'])
        if f['advisory']: items=items.filter(responses__code='A').distinct()
        header=['Assessment','Status','Rule','Created','Created by','Approved','Approved by','Y','A (Advisory)','N','Unanswered']
        rows=[]
        for a in items:
            codes=list(a.responses.values_list('code',flat=True));answered=sum(codes.count(x) for x in 'YAN')
            scope=len(a.scope_snapshot.get('requirements') or [])
            rows.append([f'v{a.version}',a.get_status_display(),a.policy_version,a.created_at.date(),a.created_by.username,a.approved_at.date() if a.approved_at else '',
                         a.approved_by.username if a.approved_by else '',codes.count('Y'),codes.count('A'),codes.count('N'),scope-answered if scope else 'Scope unknown'])
        filters=[('year','Year',[(str(y),str(y)) for y in sorted({a.created_at.year for a in Assessment.objects.filter(site=site)},reverse=True)]),
                 ('status','Status',[('draft','Draft'),('approved','Approved')]),('rule','Rule version',[('advisory-v2','advisory-v2'),('draft-v1','draft-v1')]),
                 ('auditor','Auditor',None),('advisory','Advisory',[('open','With Advisory answers')])]
    elif kind=='kz':
        items=Kaizen.objects.filter(site=site).prefetch_related('linked_requirements').order_by('-updated_at')
        f['state']=g.get('state','') if g.get('state','') in REVIEW_STATE_LABELS else ''
        f['method']=g.get('method','') if g.get('method','') in ('A4','A3','BP') else ''
        f['req']=_code(g.get('req',''))
        f['size']=g.get('size','') if g.get('size','') in ('small','medium','extensive','legacy') else ''
        f['year']=g.get('year','') if g.get('year','').isdigit() else ''
        if f['method']: items=items.filter(profile=f['method'])
        if f['req']: items=items.filter(linked_requirements__code=f['req'])
        if f['size']: items=items.filter(input_profile=f['size'])
        if f['year']: items=items.filter(created_at__year=int(f['year']))
        header=['Kaizen','Title','Type','Input view','Review state','Workflow status','Requirements','Owner','Updated']
        rows=[]
        for e in items.distinct():
            state=review_state(e)
            if f['state'] and state!=f['state']: continue
            rows.append([f'KZ-{e.pk}',e.title,e.get_profile_display(),e.get_input_profile_display(),REVIEW_STATE_LABELS[state],e.status,' '.join(r.code for r in e.linked_requirements.all()),e.data.get('owner',''),e.updated_at.date()])
        filters=[('state','Review state',list(REVIEW_STATE_LABELS.items())),('method','Type',[('A4','A4'),('A3','A3'),('BP','Business Process')]),('req','Requirement ID',None),
                 ('size','Input view',[('small','Small'),('medium','Medium'),('extensive','Extensive'),('legacy','Legacy')]),
                 ('year','Year',[(str(y),str(y)) for y in sorted({e.created_at.year for e in Kaizen.objects.filter(site=site)},reverse=True)])]
    else:
        f['cur']=g.get('cur','') if g.get('cur','') in ('current','archived') else ''
        f['req']=_code(g.get('req',''))
        f['kind']=g.get('kind','') if g.get('kind','') in ('question','documentation','governance') else ''
        rows=[]
        latest_q={}
        for v in SiteQuestionVersion.objects.filter(site=site).order_by('requirement_id','-version'):
            latest_q.setdefault(v.requirement_id,v.version)
            rows.append(('question',v.requirement_id,f'Site question v{v.version}','current' if latest_q[v.requirement_id]==v.version else 'archived',v.change_reason,v.author.username,v.created_at.date()))
        latest_p={}
        for v in PreparationNeedVersion.objects.filter(site=site).order_by('requirement_id','-version'):
            latest_p.setdefault(v.requirement_id,v.version)
            rows.append(('documentation',v.requirement_id,f'Documentation need v{v.version}','current' if latest_p[v.requirement_id]==v.version else 'archived',v.change_reason,v.author.username,v.created_at.date()))
        rows.append(('governance','','TCA Program Governance GHO-BPE-TCA-001 V.2.0 (17 Aug 2026)','current','Approval status unresolved: control says Active, footer says Draft for review.','',date(2026,8,17)))
        rows=[r for r in rows if (not f['cur'] or r[3]==f['cur']) and (not f['req'] or r[1]==f['req']) and (not f['kind'] or r[0]==f['kind'])]
        header=['Kind','Requirement','Guidance','Current / archived','Reason / note','Author','Date']
        rows=[[{'question':'Site question','documentation':'Documentation need','governance':'Governance'}[r[0]],*r[1:]] for r in rows]
        filters=[('cur','Current or archived',[('current','Current'),('archived','Archived')]),('req','Requirement ID',None),
                 ('kind','Kind',[('question','Site question'),('documentation','Documentation need'),('governance','Governance')])]
    return kind,header,rows,filters,f

@login_required
def resources(request,site_code):
    site=site_access(request,site_code)
    kind,header,rows,filters,values=report_rows(request,site)
    if request.GET.get('format')=='csv':
        return _csv(f'{dict(REPORT_TYPES)[kind].lower()}-{site.code}.csv',header,rows)
    labels={key:label for key,label,_ in filters}
    active=[(labels[key],dict(next(c for k,_,c in filters if k==key) or []).get(value,value)) for key,value in values.items() if value]
    filter_fields=[{'key':key,'label':label,'choices':choices,'value':values.get(key,'')} for key,label,choices in filters]
    return render(request,'resources.html',{'site':site,'kind':kind,'types':REPORT_TYPES,'header':header,'rows':rows,
        'primary_filters':filter_fields[:3],'more_filters':filter_fields[3:],'more_open':any(f['value'] for f in filter_fields[3:]),
        'active_filters':active,'export_query':request.GET.urlencode()})
