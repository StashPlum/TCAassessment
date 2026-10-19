"""Source-backed checks used as coach review aids, never as automatic TCA approval."""
from datetime import date
from decimal import Decimal, InvalidOperation

def results_criterion(data, observations):
    """Star 7: >30 days, >5 after points, same measure, and target or follow-up action."""
    after=[o for o in observations if o.phase=='after']
    before=[o for o in observations if o.phase=='before']
    if len(after)<=5 or not before: return False
    keys={(o.measure,o.unit,o.population) for o in after+before}
    if len(keys)!=1: return False
    dates=[o.period_start for o in after]+[o.period_end for o in after]
    if (max(dates)-min(dates)).days<=30: return False
    try:
        target=Decimal(data['target']); average=sum((o.value for o in after),Decimal(0))/len(after)
        direction=data['direction']
    except (KeyError,InvalidOperation,TypeError,ZeroDivisionError): return False
    achieved=(direction=='up' and average>=target) or (direction=='down' and average<=target)
    return bool(achieved or data.get('next_kaizen_action','').strip())

def sustain_types_criterion(data):
    return len({s.strip().lower() for s in data.get('document_types','').split(',') if s.strip()})>=2
