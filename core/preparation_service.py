"""One filtered, unpaginated data source for preparation UI and exports."""
from collections import defaultdict
from .assessment_config import current_preparation, current_question
from .models import Coverage, Opportunity, Requirement
from .readiness import accepted_codes, evidence_state


def preparation_items(site,filters,selected=None):
    current=site.assessments.first();codes,_=accepted_codes(site,current)
    reqs=Requirement.objects.select_related('category','source_version')
    if selected is not None: reqs=reqs.filter(code__in=selected)
    category=filters.get('category','');level=filters.get('level','')
    kind=filters.get('evidence_type','');owner=filters.get('owner','');due=filters.get('due')
    if str(category).isdigit(): reqs=reqs.filter(category_id=int(category))
    if level in ('C','B','A'): reqs=reqs.filter(level_code=level)
    accepted_by_req=defaultdict(set)
    coverage=Coverage.objects.filter(evidence__site=site,accepted=True).select_related('clause','evidence')
    if kind: coverage=coverage.filter(evidence__evidence_type=kind)
    for link in coverage:accepted_by_req[link.clause.requirement_id].add(link.evidence_id)
    opportunities=defaultdict(list)
    query=Opportunity.objects.filter(site=site)
    if owner:query=query.filter(owner__icontains=owner)
    if due:query=query.filter(due_date__lte=due)
    for item in query:opportunities[item.requirement_id].append(item)
    reqs=list(reqs)
    state=evidence_state(site,reqs)
    wanted=filters.get('evidence','')
    if wanted in ('missing','complete'): reqs=[r for r in reqs if state[r.code]['complete']==(wanted=='complete')]
    items=[]
    for req in reqs:
        options=opportunities.get(req.code,[])
        if (owner or due) and not options:continue
        first=options[0] if options else None
        items.append({'requirement':req,'response':codes.get(req.code,''),'accepted':len(accepted_by_req[req.code]),'evidence':state[req.code],
            'action_type':first.get_kind_display() if first else 'Pending verification',
            'owner':first.owner if first else '', 'due_date':first.due_date if first else None,
            'need':current_preparation(site,req),'question':current_question(site,req)})
    return items
