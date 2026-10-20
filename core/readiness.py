"""Accepted-response basis for the unapproved local cumulative policy."""
from django.db.models import Q
from django.utils import timezone
from .models import Clause, Coverage, Response
from .scoring import category_result
from .scoring import pass_codes

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
        eligible=row.code in pass_codes(assessment.policy_version)
        if row.code=='A' and (not row.conclusion.strip() or not row.advisory_follow_up.strip() or row.advisory_retest_status=='pending'):
            eligible=False
        if eligible and not clause_ids.get(row.requirement_id,set()).issubset(covered):
            codes[row.requirement_id]=''
            unverified.append(row.requirement_id)
        else: codes[row.requirement_id]=row.code if eligible or row.code not in pass_codes(assessment.policy_version) else ''
    return codes,unverified

def evidence_state(site, requirements, as_of=None):
    """Per requirement: clause count, clauses with accepted current evidence and linked evidence count."""
    as_of=as_of or timezone.localdate()
    codes=[r.code for r in requirements]
    clauses={}
    for req_id,clause_id in Clause.objects.filter(requirement_id__in=codes).values_list('requirement_id','id'):
        clauses.setdefault(req_id,set()).add(clause_id)
    links=Coverage.objects.filter(evidence__site=site,clause__requirement_id__in=codes)
    accepted=set(links.filter(accepted=True,reviewed_by__isnull=False,reviewed_at__isnull=False)
                 .filter(~Q(evidence__evidence_type='audit')|Q(evidence__other_audit__isnull=False))
                 .filter(Q(evidence__valid_until__isnull=True)|Q(evidence__valid_until__gte=as_of))
                 .values_list('clause_id',flat=True))
    linked={}
    for req_id,evidence_id in links.values_list('clause__requirement_id','evidence_id'):
        linked.setdefault(req_id,set()).add(evidence_id)
    return {code:{'clauses':len(clauses.get(code,())),'accepted':len(clauses.get(code,set())&accepted),
                  'linked':len(linked.get(code,())),
                  'complete':bool(clauses.get(code)) and clauses[code].issubset(accepted)} for code in codes}

def assessment_snapshot(site, assessment):
    from .models import Category
    codes,unverified=accepted_codes(site,assessment)
    coverage=list(Coverage.objects.filter(evidence__site=site,accepted=True,reviewed_by__isnull=False,reviewed_at__isnull=False)
                  .filter(~Q(evidence__evidence_type='audit')|Q(evidence__other_audit__isnull=False))
                  .filter(Q(evidence__valid_until__isnull=True)|Q(evidence__valid_until__gte=timezone.localdate()))
                  .filter(clause__requirement_id__in=[code for code,value in codes.items() if value in pass_codes(assessment.policy_version)])
                  .select_related('evidence','clause','reviewed_by').order_by('clause_id','id'))
    all_references=list(Coverage.objects.filter(evidence__site=site)
        .select_related('evidence','clause').order_by('clause_id','id'))
    categories=[]
    for cat in Category.objects.all():
        categories.append({'category':cat.number,'name':cat.name,
                           'result':category_result({r.position:codes.get(r.code,'') for r in cat.requirements.all()},assessment.policy_version)})
    return {'policy':assessment.policy_version,'approved_policy':False,'accepted_codes':codes,
            'responses':[{'requirement':r.requirement_id,'code':r.code,'conclusion':r.conclusion,
                          'advisory_follow_up':r.advisory_follow_up,'advisory_retest_status':r.advisory_retest_status,
                          'updated_by':r.updated_by_id,'updated_at':r.updated_at.isoformat()}
                         for r in assessment.responses.all().order_by('requirement_id')],
            'coverage':[{'clause_id':c.clause_id,'source_address':c.clause.source_address,
                         'evidence_id':c.evidence_id,'evidence_title':c.evidence.title,
                         'evidence_version':c.evidence.version,'decision':c.decision,
                         'reviewed_by':c.reviewed_by_id,'reviewed_at':c.reviewed_at.isoformat()}
                        for c in coverage],
            'evidence_references':[{'clause_id':link.clause_id,'source_address':link.clause.source_address,
                'evidence_id':link.evidence_id,'evidence_title':link.evidence.title,
                'evidence_version':link.evidence.version,'accepted':link.accepted,'decision':link.decision,
                'period_start':link.evidence.period_start.isoformat() if link.evidence.period_start else None,
                'period_end':link.evidence.period_end.isoformat() if link.evidence.period_end else None}
                for link in all_references],
            'unverified_yes':unverified,'categories':categories,'configuration':assessment.configuration_snapshot,
            'preparation':assessment.preparation_snapshot}
