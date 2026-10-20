"""Which requirements apply to a site: the active group-specific catalogue, or the legacy global catalogue.

Assessments freeze the resolved codes in scope_snapshot when they are created; later activation of another
catalogue never changes an existing assessment.
"""
from .models import CatalogueVersion, Requirement


class SiteSetupBlocker(Exception):
    """The site cannot start an assessment on the active catalogue until an authorised user maps its TCA group."""


def active_catalogue():
    return CatalogueVersion.objects.filter(status='active').first()


def site_group(site, catalogue=None):
    catalogue = catalogue or active_catalogue()
    if catalogue is None: return None
    group = site.tca_group
    return group if group and group.catalogue_id == catalogue.pk else None


def site_requirements(site, catalogue=None):
    """Requirements a new assessment for this site must use. Raises SiteSetupBlocker instead of guessing a group."""
    catalogue = catalogue or active_catalogue()
    if catalogue is None:
        return Requirement.objects.filter(catalogue__isnull=True)
    group = site_group(site, catalogue)
    if group is None:
        raise SiteSetupBlocker(f'{site.name} has no TCA group for {catalogue.label}. An administrator must map the site '
                               'to its TCA group before a new assessment can start.')
    return Requirement.objects.filter(catalogue=catalogue, groups=group)


def setup_blocker(site):
    try:
        site_requirements(site)
    except SiteSetupBlocker as blocker:
        return str(blocker)
    return ''


def group_preview(catalogue, group):
    """Resolved requirements for an administrator's mapping preview, with the variant check."""
    reqs = list(Requirement.objects.filter(catalogue=catalogue, groups=group).select_related('category').order_by('category_id', 'position'))
    ids = [r.question_id for r in reqs]
    variants = [r for r in reqs if Requirement.objects.filter(catalogue=catalogue, question_id=r.question_id).count() > 1]
    return {'requirements': reqs, 'count': len(reqs), 'distinct': len(set(ids)), 'variants': variants,
            'valid': len(reqs) == len(set(ids)) == 150}


def working_requirements(site):
    """Requirements the site is working towards now: the open draft's frozen scope, else the next assessment's."""
    from .progress import scope_for
    draft = site.assessments.filter(status='draft').first()
    if draft: return Requirement.objects.filter(code__in=scope_for(draft).get('requirements', []))
    try:
        return site_requirements(site)
    except SiteSetupBlocker:
        latest = site.assessments.first()
        return Requirement.objects.filter(code__in=scope_for(latest).get('requirements', [])) if latest else Requirement.objects.none()


def assessment_requirements(assessment, site=None):
    """The frozen requirement set of an assessment, or the site's working set when there is none."""
    from .progress import scope_for
    if assessment is not None: return Requirement.objects.filter(code__in=scope_for(assessment).get('requirements', []))
    return working_requirements(site) if site is not None else Requirement.objects.none()


STATE = {'Y': 'yes', 'A': 'advisory', 'N': 'no', '': 'unanswered'}
LEVEL_NAMES = {'C': 'Certified', 'B': 'Advanced', 'A': 'Showcase'}


def section_titles(requirements):
    """Section number → name as written in the requirement's own catalogue (V3 wording where present)."""
    titles = {}
    for r in requirements:
        if r.category_id not in titles: titles[r.category_id] = r.section_name
    return titles


def section_map(assessment, ordered, current_code=None):
    """15 × 10 answer map for the progress rail: one row per section, one cell per position, linked to its question."""
    answers = dict(assessment.responses.values_list('requirement_id', 'code')) if assessment else {}
    titles = section_titles(ordered)
    rows = {}
    for index, r in enumerate(ordered, 1):
        code = answers.get(r.code, '') or ''
        row = rows.setdefault(r.category_id, {'number': r.category_id, 'title': titles[r.category_id], 'cells': [], 'answered': 0})
        row['cells'].append({'requirement': r, 'page': index, 'state': STATE.get(code, 'unanswered'), 'code': code,
                             'current': r.code == current_code, 'level': r.level_code})
        row['answered'] += bool(code)
    counts = {state: sum(1 for c in answers.values() if STATE.get(c or '') == state) for state in ('yes', 'advisory', 'no')}
    counts['unanswered'] = len(ordered) - sum(counts.values())
    return {'rows': [rows[k] for k in sorted(rows)], 'counts': counts, 'total': len(ordered)}
