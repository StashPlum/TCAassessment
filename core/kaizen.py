"""Local review gates, snapshots and revision handling; no TCA scoring changes."""
from copy import deepcopy
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import KaizenRevision
from .measurements import compare_observations
from .quality import results_criterion

PROTECTED_STATES=('verified','sustained','reassessment_pending','reassessment_accepted')
REVIEW_KEYS=('coach_review',)+tuple(f'star_{i}' for i in range(1,11))
PARTICIPANT_REQUIRED=('overall_problem','specific_problem','solution','baseline','actual','unit','population','data_source','sustain')
LABELS={'overall_problem':'Overall problem','specific_problem':'Specific problem','solution':'Countermeasure',
        'baseline':'Before average','actual':'After average','unit':'Measure unit','population':'Measured population',
        'data_source':'Data source','sustain':'Sustain plan','coach_review':'Sensei review'}

def document_type_count(event):
    return len({value.strip().casefold() for value in event.document_updates.values_list('document_type',flat=True) if value.strip()})

GATE_PHASES=('Plan','Do','Check','Act')

def gate_list(event):
    """Every review gate as a structured row; review_checks() keeps the same wording for messages."""
    from .methodology import cause_analysis_required
    data=event.data
    filled=lambda key: bool(str(data.get(key,'')).strip())
    gates=[('overall_problem','Plan',filled('overall_problem')),('specific_problem','Plan',filled('specific_problem'))]
    if cause_analysis_required(event): gates.append(('root_cause','Plan',filled('root_cause')))
    gates+=[('baseline','Plan',filled('baseline')),('unit','Plan',filled('unit')),('population','Plan',filled('population')),
            ('solution','Do',filled('solution')),('do_action','Do',event.actions.filter(phase='DO').exists()),
            ('actual','Check',filled('actual')),('data_source','Check',filled('data_source')),
            ('observations','Check',any(row['difference'] is not None for row in compare_observations(event.observations.all()))),
            ('sustain','Act',filled('sustain')),('act_action','Act',event.actions.filter(phase='ACT').exists()),
            ('requests','Act',not event.review_notes.filter(kind__in=['return','clarify'],resolved=False).exists())]
    if event.data.get('star_7')=='Y': gates.append(('star_7','Check',results_criterion(event.data,list(event.observations.all()))))
    if event.data.get('star_8')=='Y': gates.append(('star_8','Act',document_type_count(event)>=2))
    return [{'key':key,'label':GATE_LABELS[key],'phase':phase,'ok':ok} for key,phase,ok in gates]

GATE_LABELS={**{key:LABELS[key] for key in PARTICIPANT_REQUIRED},'root_cause':'Cause analysis (required for A3 and Business Process)',
    'observations':'Comparable before and after observations','do_action':'Do action','act_action':'Act sustain action',
    'requests':'Sensei requests resolved','star_7':'Star 7: more than 30 days, more than five after points, comparable measures and target/follow-up',
    'star_8':'Star 8: two different document/site-tool types'}

def review_checks(event, include_coach=True):
    missing=[('Unresolved sensei requests' if gate['key']=='requests' else gate['label']) for gate in gate_list(event) if not gate['ok']]
    if include_coach and not str(event.data.get('coach_review','')).strip(): missing.insert(len(missing),LABELS['coach_review'])
    return missing

def gate_summary(event):
    gates=gate_list(event);done=sum(g['ok'] for g in gates)
    return {'gates':gates,'done':done,'total':len(gates),'percent':round(done/len(gates)*100) if gates else 0,
            'by_phase':{phase:(sum(g['ok'] for g in gates if g['phase']==phase),sum(g['phase']==phase for g in gates)) for phase in GATE_PHASES}}

REVIEW_STATE_LABELS={'draft':'Draft','in_progress':'In progress','submitted':'Submitted for review','returned':'Sensei feedback','finalised':'Finalised'}

def review_state(event):
    """Honest review state for lists and exports; derived from saved status and open sensei requests."""
    if event.status in PROTECTED_STATES: return 'finalised'
    if event.status=='results_under_review' and event.submitted_at: return 'submitted'
    if event.review_notes.filter(kind='return',resolved=False).exists(): return 'returned'
    if event.status=='proposed': return 'draft'
    return 'in_progress'

def current_phase(event):
    return {'proposed':'Plan','planned':'Do','in_progress':'Do','implemented':'Check'}.get(event.status,'Act')

def pdca_segments(event):
    """Four-segment bar: done navy, current red, all green when finalised."""
    state=review_state(event);current=current_phase(event)
    order=list(GATE_PHASES);index=order.index(current)
    return [{'phase':phase,'state':'final' if state=='finalised' else 'done' if i<index else 'current' if i==index else 'todo'} for i,phase in enumerate(order)]

def initials(name):
    parts=[p for p in name.replace('.',' ').split() if p]
    return ''.join(p[0] for p in parts[:2]).upper() or '?'

def team_display(participant):
    if participant.user_id:
        user=participant.user;full=user.get_full_name()
        return full or user.username
    return f'{participant.first_initial}. {participant.last_name}'.strip()

def snapshot(event):
    value={'title':event.title,'profile':event.profile,'input_profile':event.input_profile,'local_status':event.local_status,'status':event.status,'data':deepcopy(event.data),
           'linked_requirements':list(event.linked_requirements.values_list('code',flat=True))}
    for key in ('actions','observations','document_updates','participants','benefits','review_notes','attachments','worksheets'):
        value[key]=list(getattr(event,key).values())
    value['worksheet_history']=[dict(row) for w in event.worksheets.all() for row in w.history.values()]
    value['imports']=list(event.imports.values())
    value['reports']=list(event.a3_reports.values('id','event_revision','renderer_version','version','sha256','created_at'))
    return json.loads(json.dumps(value,cls=DjangoJSONEncoder))

def checkpoint(event,user,reason,content=None):
    value=content or snapshot(event)
    KaizenRevision.objects.get_or_create(event=event,revision=event.revision,
        defaults={'actor':user,'state':value['status'],'snapshot':value,'reason':reason})

def reopen_after_change(event):
    if event.status in PROTECTED_STATES: event.status='results_under_review'
    event.local_status='open'

def reuse_observations(event):
    """Fill empty summary fields from one measurement group; never replace entered values."""
    groups=compare_observations(event.observations.all())
    if len(groups)!=1: return
    group=groups[0]
    if any(event.data.get(key) and event.data[key]!=group[key] for key in ('measure','unit','population')): return
    for key in ('measure','unit','population'):
        if not event.data.get(key): event.data[key]=group[key]
    derived=event.data.get('derived_summary_fields',{})
    for key,average in [('baseline',group['before_average']),('actual',group['after_average'])]:
        if average is not None and (not str(event.data.get(key,'')).strip() or event.data.get(key)==derived.get(key)):
            event.data[key]=str(average)
            derived[key]=str(average)
    first=event.observations.order_by('pk').first()
    if first and not event.data.get('data_source'): event.data['data_source']=first.data_source
    event.data['derived_summary_fields']=derived
    event.data['measurement_summary_basis']='Empty summary fields derived from one measure/unit/population group; entered values retained.'

def measurement_warnings(event):
    from decimal import Decimal, InvalidOperation
    groups=compare_observations(event.observations.all())
    if len(groups)!=1: return ['Multiple measurement groups: compare equivalent measures separately.'] if groups else []
    result=[]
    for key,average in [('baseline',groups[0]['before_average']),('actual',groups[0]['after_average'])]:
        try:
            if average is not None and Decimal(event.data.get(key,''))!=average:
                result.append(f'{LABELS[key]} differs from the comparable observation average ({average}). Review the basis.')
        except InvalidOperation: pass
    return result

def changed_since_review(event):
    previous=event.history.filter(state__in=PROTECTED_STATES).first()
    if not previous: return None,[]
    changes=[LABELS.get(key,key.replace('_',' ').capitalize()) for key in sorted(set(previous.snapshot['data'])|set(event.data))
             if previous.snapshot['data'].get(key)!=event.data.get(key)]
    for key in ('actions','observations','document_updates','worksheets','attachments'):
        current=json.loads(json.dumps(list(getattr(event,key).values()),cls=DjangoJSONEncoder))
        if current!=previous.snapshot.get(key,[]): changes.append(key.replace('_',' ').capitalize())
    return previous,changes

def public_snapshot(content,financial,participants):
    value=deepcopy(content)
    if not financial: value['benefits']='Restricted'
    if not participants: value['participants']='Restricted'
    allowed={'internal'}|({'financial','hr'} if financial else set())
    value['attachments']=[a for a in value.get('attachments',[]) if a.get('classification','internal') in allowed]
    from .models import Evidence
    linked={a.get('evidence_id') for a in value['attachments'] if a.get('evidence_id')}
    visible=set(Evidence.objects.filter(pk__in=linked,classification__in=allowed).values_list('pk',flat=True))
    value['attachments']=[a for a in value['attachments'] if not a.get('evidence_id') or a['evidence_id'] in visible]
    attachment_ids={a['id'] for a in value['attachments']}
    value['imports']=[i for i in value.get('imports',[]) if i.get('attachment_id') in attachment_ids]
    return value

def gantt(actions,today):
    """Bars for the same action rows the table shows; no second planning store."""
    from datetime import timedelta
    dated=[a for a in actions if a.start_date and a.end_date]
    rows=[]
    if not dated:
        return {'rows':[{'action':a,'bar':None} for a in actions],'ticks':[],'today':None,'start':None,'end':None}
    lo=min([a.start_date for a in dated]+[today])-timedelta(days=2);hi=max([a.end_date for a in dated]+[today])+timedelta(days=2)
    span=(hi-lo).days+1;pct=lambda days: round(days/span*100,3)
    for a in actions:
        if a.start_date and a.end_date:
            width=pct((a.end_date-a.start_date).days+1)
            rows.append({'action':a,'bar':{'left':pct((a.start_date-lo).days),'width':width,'fill':round(width*min(a.progress,100)/100,3)}})
        else: rows.append({'action':a,'bar':None})
    step=7 if span<=70 else 14 if span<=140 else 28
    ticks=[{'left':pct(d),'date':lo+timedelta(days=d)} for d in range(0,span,step)]
    return {'rows':rows,'ticks':ticks,'today':pct((today-lo).days),'today_date':today,'start':lo,'end':hi}
