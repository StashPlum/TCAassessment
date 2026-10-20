"""TCA Progress 3.2 phase 3: role navigation, role start pages and server-side denial of direct requests."""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Assessment, Kaizen, KaizenAction, Membership, Opportunity, Participant, Requirement, Response, Site


def labels(response):
    return [link['label'] for group in response.context['navigation'] for link in group['links']]


class V32RoleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_catalog', verbosity=0)
        cls.site = Site.objects.create(name='Synthetic Role Site', code='v32-roles')
        cls.other = Site.objects.create(name='Synthetic Role Other', code='v32-roles-other')
        User = get_user_model()
        cls.users = {}
        for role in ('assessor', 'manager', 'coach', 'staff', 'admin'):
            user = User.objects.create_user(f'v32-{role}')
            Membership.objects.create(user=user, site=cls.site, role=role)
            cls.users[role] = user
        cls.outsider = User.objects.create_user('v32-outsider')
        Membership.objects.create(user=cls.outsider, site=cls.other, role='assessor')

    def test_navigation_is_role_specific(self):
        expected = {
            'assessor': ['Overview', 'Conduct assessment', 'Results matrix', 'Prepare evidence', 'Planning', 'History and exports',
                         'Site question versions', 'Kaizen events', 'Learning', 'Evidence library', 'Reports'],
            'manager': ['Overview', 'Results matrix', 'Section results', 'Prepare evidence', 'Planning', 'History and exports',
                        'Review queue', 'Kaizen events', 'Lean toolbox', 'Learning', 'Evidence library', 'Reports'],
            'coach': ['Overview', 'Review queue', 'Kaizen events', 'Lean toolbox', 'Learning', 'Reports'],
            'staff': ['Overview', 'Kaizen events', 'Lean toolbox', 'Learning', 'Evidence library'],
        }
        for role, items in expected.items():
            self.client.force_login(self.users[role])
            self.assertEqual(labels(self.client.get(reverse('home'))), items, role)
        self.client.force_login(self.users['admin'])
        self.assertIn('Access and configuration', labels(self.client.get(reverse('home'))))
        self.assertEqual(self.client.get(reverse('administration')).status_code, 200)

    def test_each_role_start_page_names_one_next_step(self):
        today = timezone.localdate()
        event = Kaizen.objects.create(site=self.site, title='Synthetic dock waiting', profile='A4', created_by=self.users['staff'],
                                      status='results_under_review', submitted_at=timezone.now())
        member = Participant.objects.create(event=event, user=self.users['staff'], first_initial='S', last_name='Member', kaizen_role='Kaizen lead')
        KaizenAction.objects.create(event=event, description='Synthetic measure dock times', assignee=member, end_date=today - timedelta(days=2))
        Opportunity.objects.create(site=self.site, requirement=Requirement.objects.get(pk='1.C.1'), kind='operational', problem='Synthetic overdue fix', owner='Owner', due_date=today - timedelta(days=1))
        cases = [('assessor', 'Start the first assessment'), ('manager', 'block Certified'), ('manager', 'Synthetic overdue fix'),
                 ('coach', 'Review “Synthetic dock waiting”'), ('staff', 'Synthetic measure dock times')]
        for role, text in cases:
            self.client.force_login(self.users[role])
            self.assertContains(self.client.get(reverse('home')), text, msg_prefix=role)
        self.client.force_login(self.users['assessor'])
        self.client.post(reverse('new_draft', args=[self.site.code]), {})
        self.assertContains(self.client.get(reverse('home')), 'Continue at 1.C.1')

    def test_direct_requests_are_denied_by_role_and_site(self):
        self.client.force_login(self.users['assessor'])
        self.client.post(reverse('new_draft', args=[self.site.code]), {})
        draft = Assessment.objects.get(site=self.site)
        respond = reverse('respond', args=[self.site.code, '1.C.1'])
        for role in ('coach', 'staff'):
            self.client.force_login(self.users[role])
            self.assertEqual(self.client.post(reverse('new_draft', args=[self.site.code]), {}).status_code, 404, role)
            self.assertEqual(self.client.post(respond, {'code': 'Y', 'revision': 0, 'assessment_id': draft.pk}).status_code, 404, role)
            self.assertEqual(self.client.post(reverse('approve', args=[self.site.code]), {'confirm_partial': 'on'}).status_code, 404, role)
            self.assertEqual(self.client.get(reverse('administration')).status_code, 404, role)
        self.client.force_login(self.users['staff'])
        self.assertEqual(self.client.get(reverse('review_queue', args=[self.site.code])).status_code, 404)
        self.client.force_login(self.outsider)
        for url in (reverse('assessment', args=[self.site.code]), reverse('site', args=[self.site.code]), reverse('kaizens', args=[self.site.code]),
                    reverse('evidence', args=[self.site.code]), reverse('assessment_history', args=[self.site.code])):
            self.assertEqual(self.client.get(url).status_code, 404, url)
        self.assertEqual(self.client.post(respond, {'code': 'Y', 'revision': 0, 'assessment_id': draft.pk}).status_code, 404)
        self.assertEqual(self.client.post(reverse('new_draft', args=[self.site.code]), {}).status_code, 404)
        self.assertFalse(Response.objects.filter(assessment=draft).exists())
        # Site selection never grants rights: posting another site's code to the switcher is refused.
        self.assertEqual(self.client.post(reverse('switch_site'), {'site_code': self.site.code}).status_code, 404)
