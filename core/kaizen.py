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

def review_checks(event, include_coach=True):
    required=PARTICIPANT_REQUIRED+(('coach_review',) if include_coach else ())
    missing=[LABELS[key] for key in required if not str(event.data.get(key,'')).strip()]
    if not any(row['difference'] is not None for row in compare_observations(event.observations.all())):
        missing.append('Comparable before and after observations')
    if not event.actions.filter(phase='DO').exists(): missing.append('Do action')
    if not event.actions.filter(phase='ACT').exists(): missing.append('Act sustain action')
    if event.data.get('star_7')=='Y' and not results_criterion(event.data,list(event.observations.all())):
        missing.append('Star 7: more than 30 days, more than five after points, comparable measures and target/follow-up')
    if event.data.get('star_8')=='Y' and document_type_count(event)<2:
        missing.append('Star 8: two different document/site-tool types')
    if event.review_notes.filter(kind__in=['return','clarify'],resolved=False).exists(): missing.append('Unresolved sensei requests')
    return missing

def snapshot(event):
    value={'title':event.title,'profile':event.profile,'status':event.status,'data':deepcopy(event.data),
           'linked_requirements':list(event.linked_requirements.values_list('code',flat=True))}
    for key in ('actions','observations','document_updates','participants','benefits','review_notes'):
        value[key]=list(getattr(event,key).values())
    return json.loads(json.dumps(value,cls=DjangoJSONEncoder))

def checkpoint(event,user,reason,content=None):
    value=content or snapshot(event)
    KaizenRevision.objects.get_or_create(event=event,revision=event.revision,
        defaults={'actor':user,'state':value['status'],'snapshot':value,'reason':reason})

def reopen_after_change(event):
    if event.status in PROTECTED_STATES: event.status='results_under_review'

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
    for key in ('actions','observations','document_updates'):
        current=json.loads(json.dumps(list(getattr(event,key).values()),cls=DjangoJSONEncoder))
        if current!=previous.snapshot.get(key,[]): changes.append(key.replace('_',' ').capitalize())
    return previous,changes

def public_snapshot(content,financial,participants):
    value=deepcopy(content)
    if not financial: value['benefits']='Restricted'
    if not participants: value['participants']='Restricted'
    return value
