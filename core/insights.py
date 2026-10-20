"""Decision-first visual data for role start pages. Every figure comes from stored records; nothing is estimated.

maturity_ladder  Site manager: which cumulative gate each section meets, which section is lowest, what blocks next.
action_timeline  Manager / team member: open actions and Kaizen tasks on a dated axis, overdue left of today.
review_pipeline  Sensei: Kaizen events per review state, from the saved workflow state.
outcome_checks   Sensei: before/after measurements per event (no target or trend is invented).
"""
from datetime import timedelta
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from .catalogue import assessment_requirements, section_titles
from .kaizen import REVIEW_STATE_LABELS, review_state
from .models import Kaizen, KaizenAction, Observation, Opportunity
from .readiness import accepted_codes
from .scoring import category_result, pass_codes

BANDS = (('Certified', 1, 5), ('Advanced', 6, 8), ('Showcase', 9, 10))
RANK = {None: 0, 'Certified': 1, 'Advanced': 2, 'Showcase': 3}


def maturity_ladder(site, assessment):
    """One row per section: passes per band, the level earned under the cumulative rule and the lowest section."""
    if assessment is None: return None
    reqs = list(assessment_requirements(assessment).select_related('category'))
    if not reqs: return None
    codes, _ = accepted_codes(site, assessment)
    answers = dict(assessment.responses.values_list('requirement_id', 'code'))
    passing = pass_codes(assessment.policy_version)
    titles = section_titles(reqs)
    rows = []
    for number in sorted(titles):
        items = {r.position: r for r in reqs if r.category_id == number}
        result = category_result({p: codes.get(r.code, '') for p, r in items.items()}, assessment.policy_version)
        bands = []
        for name, first, last in BANDS:
            cells = [items[p] for p in range(first, last + 1) if p in items]
            passed = sum(1 for r in cells if codes.get(r.code) in passing)
            pending = sum(1 for r in cells if answers.get(r.code) in passing and codes.get(r.code) not in passing)
            bands.append({'name': name, 'passed': passed, 'total': len(cells), 'pending': pending,
                          'met': RANK[result['earned']] >= RANK[name]})
        rows.append({'number': number, 'title': titles[number], 'earned': result['earned'], 'bands': bands})
    lowest_rank = min(RANK[r['earned']] for r in rows)
    next_level = next((name for name, rank in (('Certified', 1), ('Advanced', 2), ('Showcase', 3)) if rank > lowest_rank), None)
    shared = sum(1 for r in rows if RANK[r['earned']] == lowest_rank)
    for row in rows:
        # Flag the lowest section only when it stands out; when most sections share it the flag is noise.
        row['lowest'] = RANK[row['earned']] == lowest_rank and shared <= len(rows) // 2
        row['blocks_next'] = next_level is not None and RANK[row['earned']] < RANK[next_level]
    return {'rows': rows, 'lowest': next(n for n, rank in RANK.items() if rank == lowest_rank), 'next_level': next_level,
            'blocking_sections': sum(r['blocks_next'] for r in rows), 'assessment': assessment,
            'policy': assessment.policy_version}


def action_timeline(site, user=None, today=None, weeks_ahead=8):
    """Open, dated work items. With a user, only that person's Kaizen tasks and actions."""
    today = today or timezone.localdate()
    items = []
    opportunities = Opportunity.objects.filter(site=site, status='open', due_date__isnull=False)
    tasks = KaizenAction.objects.filter(event__site=site, end_date__isnull=False).exclude(progress=100).select_related('event')
    if user is not None:
        opportunities = opportunities.filter(owner__iexact=user.username)
        tasks = tasks.filter(Q(assignee__user=user) | Q(assignee__isnull=True, owner__iexact=user.username))
    for o in opportunities:
        items.append({'kind': 'Action', 'title': o.problem, 'owner': o.owner or 'Owner not set', 'due': o.due_date,
                      'label': o.requirement.label if o.requirement else '', 'progress': None,
                      'url': reverse('opportunities', args=[site.code]) + '#work-list'})
    for t in tasks:
        items.append({'kind': 'Kaizen task', 'title': t.description, 'owner': t.owner, 'due': t.end_date, 'start': t.start_date,
                      'label': t.event.title, 'progress': t.progress, 'url': reverse('kaizen_detail', args=[site.code, t.event_id])})
    if not items: return {'items': [], 'today': today}
    start = min(min(i['due'] for i in items), today - timedelta(days=7))
    end = max(today + timedelta(weeks=weeks_ahead), max(i['due'] for i in items))
    span = max((end - start).days, 1)
    for i in items:
        i['overdue'] = i['due'] < today
        i['soon'] = not i['overdue'] and i['due'] <= today + timedelta(days=14)
        i['x'] = round(100 * (i['due'] - start).days / span, 2)
        i['days'] = (i['due'] - today).days
    items.sort(key=lambda i: i['due'])
    ticks = []
    tick = start - timedelta(days=start.weekday())
    while tick <= end:
        x = round(100 * (tick - start).days / span, 2)
        # Skip ticks that would sit under the "Today" label.
        if tick >= start and abs(x - 100 * (today - start).days / span) > 9: ticks.append({'date': tick, 'x': x})
        tick += timedelta(weeks=2)
    return {'items': items, 'today': today, 'today_x': round(100 * (today - start).days / span, 2), 'ticks': ticks,
            'overdue': sum(i['overdue'] for i in items), 'soon': sum(i['soon'] for i in items), 'start': start, 'end': end}


PIPELINE = ('draft', 'in_progress', 'submitted', 'returned', 'finalised')


def review_pipeline(site):
    """Count of Kaizen events per review state, oldest submission first in the 'submitted' column."""
    columns = {state: [] for state in PIPELINE}
    for event in Kaizen.objects.filter(site=site).prefetch_related('review_notes').order_by('-updated_at'):
        columns[review_state(event)].append(event)
    columns['submitted'].sort(key=lambda e: e.submitted_at or e.updated_at)
    total = sum(len(v) for v in columns.values())
    return {'columns': [{'state': s, 'label': REVIEW_STATE_LABELS[s], 'events': columns[s][:4], 'count': len(columns[s]),
                         'share': round(100 * len(columns[s]) / total, 1) if total else 0} for s in PIPELINE], 'total': total}


def outcome_checks(site, limit=6):
    """Before/after pairs with the same measure and unit; events without both sides are listed as missing results."""
    rows = []
    for event in Kaizen.objects.filter(site=site).prefetch_related('observations').order_by('-updated_at'):
        obs = list(event.observations.all())
        if not obs: continue
        by_measure = {}
        for o in obs: by_measure.setdefault((o.measure, o.unit), {}).setdefault(o.phase, o)
        for (measure, unit), sides in by_measure.items():
            before, after = sides.get('before'), sides.get('after')
            if not before: continue
            values = [float(before.value)] + ([float(after.value)] if after else [])
            low, high = min(values + [0.0]), max(values) or 1.0
            scale = lambda v: round(100 * (v - low) / ((high - low) or 1), 1)
            rows.append({'event': event, 'measure': measure, 'unit': unit, 'before': before, 'after': after,
                         'before_x': scale(float(before.value)), 'after_x': scale(float(after.value)) if after else None,
                         'change': (float(after.value) - float(before.value)) if after else None})
        if len(rows) >= limit: break
    return rows[:limit]
