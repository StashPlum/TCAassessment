"""Read-only assessment answer matrix for the frozen effective scope."""
from .models import Category, Requirement
from .progress import scope_for


def assessment_matrix(assessment):
    scope=scope_for(assessment)
    codes=scope.get('requirements',[])
    if not isinstance(codes,list) or len(codes)!=len(set(codes)):
        codes=[]
    requirements=list(Requirement.objects.filter(code__in=codes).select_related('category').order_by('category_id','position'))
    in_scope={r.code for r in requirements}
    positions=sorted({r.position for r in requirements})
    responses={r.requirement_id:r for r in assessment.responses.select_related('requirement')} if assessment else {}
    groups=[]
    for title,position_set in [('Certified',range(1,6)),('Advanced',range(6,9)),('Showcase',range(9,11))]:
        included=[position for position in positions if position in position_set]
        if included: groups.append({'title':title,'count':len(included)})
    rows=[]
    for category in Category.objects.all().order_by('number'):
        by_position={r.position:r for r in requirements if r.category_id==category.pk}
        if not by_position: continue
        cells=[]
        for position in positions:
            req=by_position.get(position)
            response=responses.get(req.code) if req else None
            code=response.code if response and response.code in ('Y','A','N') else ''
            cells.append({'requirement':req,'position':position,'code':code,
                          'label':{'Y':'Y · Yes','A':'A · Advisory','N':'N · No','':'Unanswered'}[code] if req else 'Outside scope',
                          'state':{'Y':'yes','A':'advisory','N':'no','':'unanswered'}[code] if req else 'outside'})
        rows.append({'category':category,'cells':cells})
    return {'rows':rows,'categories':[row['category'] for row in rows],
            'positions':positions,'groups':groups,'scope':scope,
            'requirements_count':len(in_scope),'sections_count':len(rows),
            'known':bool(scope.get('known')) and len(in_scope)==len(codes)}
