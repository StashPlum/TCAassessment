"""Role-specific navigation. Menus only decide what is shown; every view still checks access on the server."""
from django.urls import reverse

# (label, url name, routes that mark the item active, roles that see it)
ASSESSORS = {'assessor'}
RESULTS = {'assessor', 'manager', 'admin'}
KAIZEN = {'assessor', 'manager', 'coach', 'staff', 'admin'}
SENSEI = {'coach', 'manager', 'admin'}

NAVIGATION = (
    ('My work', (
        ('Overview', 'home', ('home',), KAIZEN),
    )),
    ('Assessment', (
        ('Conduct assessment', 'assessment', ('assessment', 'respond'), ASSESSORS),
        ('Results matrix', 'opportunities', ('opportunities',), RESULTS),
        ('Section results', 'site', ('site',), {'manager', 'admin'}),
        ('Prepare evidence', 'preparation', ('preparation', 'preparation_need'), ASSESSORS | {'manager'}),
        ('Planning', 'sessions', ('sessions', 'session_detail'), ASSESSORS | {'manager'}),
        ('History and exports', 'assessment_history', ('assessment_history',), RESULTS),
        ('Site question versions', 'assessment_configuration', ('assessment_configuration', 'question_configuration'), ASSESSORS),
    )),
    ('Improvement', (
        ('Review queue', 'review_queue', ('review_queue', 'kaizen_review_detail'), SENSEI),
        ('Kaizen events', 'kaizens', ('kaizens', 'kaizen_detail', 'kaizen_template_details', 'toolbox', 'worksheet', 'a3_preview'), KAIZEN),
        ('Lean toolbox', 'toolbox_library', ('toolbox_library',), {'coach', 'staff', 'manager'}),
    )),
    ('Knowledge & evidence', (
        ('Learning', 'learning', ('learning', 'learning_publish'), KAIZEN),
        ('Evidence library', 'evidence', ('evidence', 'other_audit', 'claims', 'claim_review'), ASSESSORS | {'manager', 'staff', 'admin'}),
        ('Reports', 'resources', ('resources',), RESULTS | {'coach'}),
    )),
)

def navigation(roles, site, current_route, can_administer=False):
    """Groups of links for the union of the user's roles at the selected site, in task order."""
    groups = []
    if site:
        for heading, items in NAVIGATION:
            links = [{'label': label, 'url': reverse(name) if name == 'home' else reverse(name, args=[site.code]),
                      'active': current_route in routes}
                     for label, name, routes, allowed in items if roles & allowed]
            if links: groups.append({'heading': heading, 'links': links})
    if can_administer:
        groups.append({'heading': 'Administration', 'links': [{'label': 'Access and configuration', 'url': reverse('administration'), 'active': current_route == 'administration'}]})
    return groups
