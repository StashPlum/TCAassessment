"""Accepted-response basis for the unapproved local cumulative policy."""
from django.db.models import Q
from django.utils import timezone
from .models import Clause, Coverage, Response
from .scoring import category_result

def accepted_codes(site, assessment, as_of=None):
    if assessment is None: return {},[]
    as_of=as_of or timezone.localdate()
    covered=set(Coverage.objects.filter(evidence__site=site,accepted=True,reviewed_by__isnull=False,reviewed_at__isnull=False)
                .filter(~Q(evidence__evidence_type='audit')|Q(evidence__other_audit__isnull=False))
                .filter(Q(evidence__valid_until__isnull=True)|Q(evidence__valid_until__gte=as_of))
                .values_list('clause_id',flat=True))
    clause_ids={}
    for req_id,clause_id in Clause.objects.values_list('requirement_id','id'):
        clause_ids.setdefault(req_id,set()).add(clause_id)
    codes={};unverified=[]
    for row in assessment.responses.all():
        if row.code=='Y' and not clause_ids.get(row.requirement_id,set()).issubset(covered):
            codes[row.requirement_id]=''
            unverified.append(row.requirement_id)
        else: codes[row.requirement_id]=row.code
    return codes,unverified

def assessment_snapshot(site, assessment):
    from .models import Category
    codes,unverified=accepted_codes(site,assessment)
    coverage=list(Coverage.objects.filter(evidence__site=site,accepted=True,reviewed_by__isnull=False,reviewed_at__isnull=False)
                  .filter(~Q(evidence__evidence_type='audit')|Q(evidence__other_audit__isnull=False))
                  .filter(Q(evidence__valid_until__isnull=True)|Q(evidence__valid_until__gte=timezone.localdate()))
                  .filter(clause__requirement_id__in=[code for code,value in codes.items() if value=='Y'])
                  .select_related('evidence','clause','reviewed_by').order_by('clause_id','id'))
    categories=[]
    for cat in Category.objects.all():
        categories.append({'category':cat.number,'name':cat.name,
                           'result':category_result({r.position:codes.get(r.code,'') for r in cat.requirements.all()})})
    return {'policy':'draft-v1','approved_policy':False,'accepted_codes':codes,
            'responses':[{'requirement':r.requirement_id,'code':r.code,'conclusion':r.conclusion,
                          'updated_by':r.updated_by_id,'updated_at':r.updated_at.isoformat()}
                         for r in assessment.responses.all().order_by('requirement_id')],
            'coverage':[{'clause_id':c.clause_id,'source_address':c.clause.source_address,
                         'evidence_id':c.evidence_id,'evidence_title':c.evidence.title,
                         'evidence_version':c.evidence.version,'decision':c.decision,
                         'reviewed_by':c.reviewed_by_id,'reviewed_at':c.reviewed_at.isoformat()}
                        for c in coverage],
            'unverified_yes':unverified,'categories':categories}
