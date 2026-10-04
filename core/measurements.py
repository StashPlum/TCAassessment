"""Comparable before/after measurements and nonduplicated event benefits."""
from collections import defaultdict
from decimal import Decimal

def compare_observations(observations):
    groups=defaultdict(lambda:{'before':[],'after':[]})
    for item in observations:
        key=(item.measure,item.unit,item.population)
        groups[key][item.phase].append(Decimal(item.value))
    results=[]
    for (measure,unit,population), phases in groups.items():
        before,after=phases['before'],phases['after']
        results.append({'measure':measure,'unit':unit,'population':population,'before_count':len(before),
                        'after_count':len(after),'before_average':sum(before)/len(before) if before else None,
                        'after_average':sum(after)/len(after) if after else None,
                        'difference':(sum(after)/len(after)-sum(before)/len(before)) if before and after else None})
    return results

def event_benefits(benefits):
    """Count each event record once, independent of its linked TCA requirements."""
    totals=defaultdict(Decimal)
    for benefit in benefits:
        if benefit.validated: totals[(benefit.kind,benefit.unit)]+=benefit.amount
    return dict(totals)
