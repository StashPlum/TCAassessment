"""Completeness rules applied when a draft assessment is approved (drafts may be incomplete)."""
from .models import Requirement
from .readiness import evidence_state
from .scoring import pass_codes

def approval_problems(site, assessment, allow_unanswered=False):
    """Return actionable messages that block approval; empty means the draft may be approved."""
    from .progress import scope_for
    scope = scope_for(assessment).get('requirements', [])
    order = {code: i for i, code in enumerate(scope)}
    _codes = lambda codes: ', '.join(code.split('~')[0] for code in sorted(codes, key=lambda code: order.get(code, len(order))))
    rows = {r.requirement_id: r for r in assessment.responses.all()}
    passing = pass_codes(assessment.policy_version)
    problems = []
    unanswered = [code for code in scope if code not in rows or rows[code].code not in ('Y', 'A', 'N')]
    if unanswered and not allow_unanswered:
        problems.append(f'{len(unanswered)} of {len(scope)} questions have no answer ({_codes(unanswered[:12])}{" …" if len(unanswered) > 12 else ""}). '
                        'Answer them, or confirm that this dated record covers only part of the assessment.')
    no_conclusion = [code for code, r in rows.items() if r.code in passing and not r.conclusion.strip()]
    if no_conclusion:
        problems.append(f'Add a conclusion for {_codes(no_conclusion)}. A pass needs your evidence-based reasoning so the decision can be audited later.')
    no_follow_up = [code for code, r in rows.items() if r.code == 'A' and not r.advisory_follow_up.strip()]
    if no_follow_up:
        problems.append(f'Describe the improvement and next check for Advisory {_codes(no_follow_up)}. Without it the Advisory cannot be followed up.')
    pending_retest = [code for code, r in rows.items() if r.advisory_retest_status == 'pending']
    if pending_retest:
        problems.append(f'Decide again on the earlier Advisory for {_codes(pending_retest)}. A previous Advisory is never carried over automatically.')
    claimed = [code for code, r in rows.items() if r.code in passing]
    evidence = evidence_state(site, list(Requirement.objects.filter(code__in=claimed)))
    lacking = [code for code in claimed if not evidence[code]['complete']]
    if lacking:
        problems.append(f'Link accepted, current evidence to every clause of {_codes(lacking)}, or change the answer. '
                        'Y and Advisory count as a pass only with accepted evidence.')
    return problems
