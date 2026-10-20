"""The assessment journey (prepare → plan → conduct → review → results) derived from recorded data only."""
from django.utils import timezone
from .models import AssessmentSession, Requirement


def assessment_journey(site, assessment, answered=None, total=None):
    """Five stages with a state (done, current, attention, todo) and one short fact each; nothing is estimated."""
    from .progress import scope_for
    from .readiness import evidence_state
    draft = assessment if assessment and assessment.status == 'draft' else None
    scope = scope_for(assessment).get('requirements', []) if assessment else []
    if answered is None and assessment is not None:
        answered = assessment.responses.filter(code__in=('Y', 'A', 'N'), requirement_id__in=scope).count()
    total = total if total is not None else len(scope)
    evidence = evidence_state(site, list(Requirement.objects.filter(code__in=scope))) if scope else {}
    complete = sum(1 for e in evidence.values() if e['complete'])
    confirmed = AssessmentSession.objects.filter(site=site, availability='confirmed').exists()
    planned = AssessmentSession.objects.filter(site=site, date__gte=timezone.localdate()).exists()
    problems = []
    if draft:
        from .assessment_rules import approval_problems
        problems = approval_problems(site, draft)
    approved = assessment is not None and assessment.status == 'approved'
    steps = [
        {'key': 'prepare', 'label': 'Prepare evidence', 'url_name': 'preparation',
         'fact': f'{complete} of {total} with complete evidence' if total else 'No questions yet',
         'state': 'done' if total and complete == total else 'todo'},
        {'key': 'plan', 'label': 'Plan', 'url_name': 'sessions',
         'fact': 'Session confirmed' if confirmed else 'Session proposed' if planned else 'Optional',
         'state': 'done' if confirmed else 'todo'},
        {'key': 'conduct', 'label': 'Conduct', 'url_name': 'assessment',
         'fact': f'{answered} of {total} answered' if assessment else 'Not started',
         'state': 'done' if approved or (draft and total and answered == total) else 'current' if draft else 'todo'},
        {'key': 'review', 'label': 'Review and approve', 'url_name': 'assessment',
         'fact': ('Approved' if approved else f'{len(problems)} item{"s" if len(problems) != 1 else ""} to resolve' if problems else 'Ready to approve') if assessment else 'After conducting',
         'state': 'done' if approved else 'attention' if draft and problems and total and answered == total else 'current' if draft and not problems else 'todo'},
        {'key': 'results', 'label': 'Results', 'url_name': 'opportunities',
         'fact': f'v{assessment.version} approved' if approved else 'After approval',
         'state': 'done' if approved else 'todo'},
    ]
    return {'steps': steps, 'problems': problems}
