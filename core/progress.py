"""Requirements coverage, frozen scope and local gates; never official CAT standing."""
from django.utils import timezone
from django.db.models import Count
from .models import Requirement,ApplicabilityException,VerificationClaim,Kaizen,AssessmentSession,Opportunity
from .readiness import accepted_codes
from .scoring import category_result,pass_codes

def baseline_scope():
    rows=list(Requirement.objects.select_related('source_version'))
    hashes={r.source_version.sha256 for r in rows}
    return {'version':'global-'+next(iter(hashes))[:12] if len(hashes)==1 else 'unknown',
            'source_hash':next(iter(hashes)) if len(hashes)==1 else None,
            'requirements':[r.code for r in rows],'basis':'Original global baseline; no applicability subtraction',
            'known':len(hashes)==1 and bool(rows),'frozen_at':timezone.now().isoformat()}

def scope_for(assessment):
    if assessment and assessment.scope_snapshot: return assessment.scope_snapshot
    scope=baseline_scope()
    scope['basis']='Legacy assessment: original global baseline inferred; governed assignment not recorded'
    return scope

def fraction(numerator,denominator,known=True):
    return {'count':numerator,'total':denominator if known else None,
            'percent':round(100*numerator/denominator,2) if known and denominator else None}

def coverage_progress(site,baseline=None,as_of=None):
    now=as_of or timezone.localdate();current=site.assessments.first()
    baseline=baseline or site.assessments.filter(status='approved').order_by('version').first()
    scope=scope_for(current);codes=scope.get('requirements',[])
    if not isinstance(codes,list) or len(set(codes))!=len(codes): codes=[];scope={**scope,'known':False}
    reqs=list(Requirement.objects.filter(pk__in=codes).select_related('category'))
    event_links={}
    for event in Kaizen.objects.filter(site=site).prefetch_related('linked_requirements'):
        for req in event.linked_requirements.all(): event_links.setdefault(req.code,[]).append(event)
    action_links={}
    for action in Opportunity.objects.filter(site=site,status='open'):
        action_links.setdefault(action.requirement_id,[]).append(action)
    for req in reqs:
        req.contributing_events=event_links.get(req.code,[]);req.contributing_actions=action_links.get(req.code,[])
    known=bool(scope.get('known')) and len(reqs)==len(codes)
    notes=[]
    if ApplicabilityException.objects.filter(site=site).exists():
        known=False;notes.append('Applicability exceptions exist; their denominator arithmetic is unapproved. No adjusted percentage is asserted.')
    if not known: notes.append('The applicable denominator is not confirmed.')
    if not codes: notes.append('Empty scope: no 100% coverage claim.')
    accepted,unverified=accepted_codes(site,current,now);passing=pass_codes(current.policy_version) if current else set()
    ys={r.code for r in reqs if accepted.get(r.code) in passing}
    pending=set(VerificationClaim.objects.filter(site=site,status='pending',requirement_id__in=codes).values_list('requirement_id',flat=True))-ys
    base_scope=scope_for(baseline);same_scope=(base_scope.get('version')==scope.get('version') and set(base_scope.get('requirements',[]))==set(codes))
    baseline_ys={code for code,value in (baseline.snapshot.get('accepted_codes',{}) if baseline else {}).items() if value in pass_codes(baseline.policy_version) and code in base_scope.get('requirements',[])}
    base_known=bool(base_scope.get('known'))
    if baseline and not same_scope: notes.append('Baseline and current scope/template differ: percentages are not a comparable trend.')
    sections=[];local_levels=[]
    threshold={'C':5,'B':8,'A':10}[site.target_level]
    for category in sorted({r.category_id for r in reqs}):
        items=[r for r in reqs if r.category_id==category];missing=[r for r in items if r.code not in ys]
        result=category_result({r.position:accepted.get(r.code,'') for r in items},current.policy_version if current else 'draft-v1')
        local_levels.append(result['earned'])
        gate=[r for r in items if r.position<=threshold]
        sections.append({'category':items[0].category,'coverage':fraction(len(items)-len(missing),len(items),known),
                         'gate':fraction(sum(r.code in ys for r in gate),len(gate),known),'blockers':[r for r in gate if r.code not in ys],
                         'result':result,'pending':len([r for r in items if r.code in pending])})
    target_items=[r for r in reqs if r.position<=threshold]
    responses=list(current.responses.filter(requirement_id__in=codes)) if current else []
    assessed={r.requirement_id for r in responses if r.code in ('Y','A','N')}
    advisory={r.requirement_id for r in responses if r.code=='A'}
    ranking={'Certified':1,'Advanced':2,'Showcase':3,None:0}
    lowest=min(local_levels,key=lambda v:ranking[v]) if local_levels and known else None
    return {'current':current,'baseline':baseline,'scope':scope,'as_of':now,'coverage':fraction(len(ys),len(codes),known),
            'assessed':fraction(len(assessed),len(codes),known),'open_advisory_count':len(advisory),
            'answer_policy':current.policy_version if current else None,
            'baseline_coverage':fraction(len(baseline_ys),len(base_scope.get('requirements',[])),base_known),
            'comparable':same_scope,'pending_count':len(pending),'pending_percent':100*len(pending)/len(codes) if known and codes else 0,
            'sections':sections,'target':fraction(sum(r.code in ys for r in target_items),len(target_items),known),
            'lowest_local':lowest,'notes':notes,'unverified':unverified,
            'events':list(Kaizen.objects.filter(site=site).values('input_profile','local_status').annotate(count=Count('pk'))),
            'sessions':AssessmentSession.objects.filter(site=site).order_by('date')[:20],
            'sustain':Kaizen.objects.filter(site=site).order_by('-updated_at')[:20]}

def progress_export(progress):
    return {k:progress[k] for k in ('coverage','assessed','open_advisory_count','answer_policy','baseline_coverage','pending_count','scope','comparable','notes','target','lowest_local','unverified')}|{
        'as_of':str(progress['as_of']),'classification':'Local versioned policy only; CAT confirmation and frequency policy pending',
        'sections':[{'category':s['category'].pk,'coverage':s['coverage'],'gate':s['gate'],'result':s['result'],'blockers':[r.code for r in s['blockers']]} for s in progress['sections']]}
