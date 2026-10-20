"""TCA Progress 3.2 phase 6: server-side denial matrix for every site route, per role and for other sites.

Hidden buttons are not authorization: each request below is sent directly, as a user who should not be able to act.
"""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import (Assessment, AssessmentSession, Benefit, Coverage, Evidence, Kaizen, KaizenAction, Membership,
                     Participant, Requirement, Response, Site, Worksheet)

DENIED = (403, 404, 405)
WATCHED = (Assessment, Response, Evidence, Coverage, AssessmentSession, Kaizen, KaizenAction, Benefit, Worksheet, Participant)


class V32RbacMatrixTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_catalog', verbosity=0)
        User = get_user_model()
        cls.site = Site.objects.create(name='Synthetic RBAC Site', code='v32-rbac')
        cls.other = Site.objects.create(name='Synthetic RBAC Other', code='v32-rbac-other')
        cls.users = {}
        for role in ('assessor', 'manager', 'coach', 'staff', 'admin'):
            cls.users[role] = User.objects.create_user(f'rbac-{role}')
            Membership.objects.create(user=cls.users[role], site=cls.site, role=role)
        # The outsider holds every role, but only at the other site.
        cls.outsider = User.objects.create_user('rbac-outsider')
        for role in ('assessor', 'manager', 'coach', 'staff'):
            Membership.objects.create(user=cls.outsider, site=cls.other, role=role)
        a = cls.users['assessor']
        cls.draft = Assessment.objects.create(site=cls.site, version=1, created_by=a, policy_version='advisory-v2')
        cls.req = Requirement.objects.get(pk='1.C.1')
        cls.evidence = Evidence.objects.create(site=cls.site, title='Synthetic RBAC evidence', evidence_type='document', owner='Fixture', created_by=a)
        cls.coverage = Coverage.objects.create(evidence=cls.evidence, clause=cls.req.clauses.first())
        cls.session = AssessmentSession.objects.create(site=cls.site, date=timezone.localdate(), method='On site')
        cls.event = Kaizen.objects.create(site=cls.site, title='Synthetic RBAC Kaizen', profile='A4', created_by=cls.users['staff'])
        member = Participant.objects.create(event=cls.event, user=cls.users['staff'], first_initial='S', last_name='Member', kaizen_role='Kaizen lead')
        cls.action = KaizenAction.objects.create(event=cls.event, description='Synthetic RBAC task', assignee=member)
        cls.worksheet = Worksheet.objects.create(event=cls.event, method='5w2h', stage='Plan', title='5W2H')
        cls.benefit = Benefit.objects.create(event=cls.event, kind='hours', amount=1, unit='h')

    def routes(self):
        s, e = self.site.code, self.event.pk
        return {
            'site': reverse('site', args=[s]), 'assessment': reverse('assessment', args=[s]),
            'assessment_configuration': reverse('assessment_configuration', args=[s]),
            'question_configuration': reverse('question_configuration', args=[s, self.req.code]),
            'respond': reverse('respond', args=[s, self.req.code]), 'approve': reverse('approve', args=[s]),
            'new_draft': reverse('new_draft', args=[s]), 'assessment_archive': reverse('assessment_archive', args=[s]),
            'assessment_history': reverse('assessment_history', args=[s]),
            'assessment_history_export': reverse('assessment_history_export', args=[s, 'xlsx']),
            'sessions': reverse('sessions', args=[s]), 'session_detail': reverse('session_detail', args=[s, self.session.pk]),
            'opportunities': reverse('opportunities', args=[s]), 'kaizens': reverse('kaizens', args=[s]),
            'review_queue': reverse('review_queue', args=[s]), 'review_export': reverse('review_export', args=[s, 'csv']),
            'kaizen_detail': reverse('kaizen_detail', args=[s, e]), 'kaizen_autosave': reverse('kaizen_autosave', args=[s, e]),
            'review_note': reverse('review_note', args=[s, e]), 'kaizen_review_detail': reverse('kaizen_review_detail', args=[s, e]),
            'kaizen_add': reverse('kaizen_add', args=[s, e, 'benefit']),
            'kaizen_action_edit': reverse('kaizen_action_edit', args=[s, e, self.action.pk]),
            'task_progress': reverse('task_progress', args=[s, e, self.action.pk]),
            'kaizen_template_details': reverse('kaizen_template_details', args=[s, e]),
            'validate_benefit': reverse('validate_benefit', args=[s, self.benefit.pk]),
            'kaizen_archive': reverse('kaizen_archive', args=[s, e]), 'kaizen_excel': reverse('kaizen_excel', args=[s, e]),
            'event_export': reverse('event_export', args=[s, e, 'json']), 'event_archive_zip': reverse('event_archive_zip', args=[s, e]),
            'a3_preview': reverse('a3_preview', args=[s, e]), 'a3_finalize': reverse('a3_finalize', args=[s, e]),
            'learning_publish': reverse('learning_publish', args=[s, e]),
            'toolbox': reverse('toolbox', args=[s, e]), 'worksheet': reverse('worksheet', args=[s, e, self.worksheet.pk]),
            'worksheet_export': reverse('worksheet_export', args=[s, e, self.worksheet.pk, 'json']),
            'input_profile': reverse('input_profile', args=[s, e]), 'attachment_add': reverse('attachment_add', args=[s, e]),
            'import_preview': reverse('import_preview', args=[s, e]),
            'evidence': reverse('evidence', args=[s]), 'preparation': reverse('preparation', args=[s]),
            'preparation_export': reverse('preparation_export', args=[s, 'xlsx']),
            'preparation_need': reverse('preparation_need', args=[s, self.req.code]),
            'other_audit': reverse('other_audit', args=[s, self.evidence.pk]), 'link_evidence': reverse('link_evidence', args=[s, self.evidence.pk]),
            'evidence_link_requirement': reverse('evidence_link_requirement', args=[s, self.evidence.pk]),
            'download': reverse('download', args=[s, self.evidence.pk]), 'review_coverage': reverse('review_coverage', args=[s, self.coverage.pk]),
            'report': reverse('report', args=[s]), 'resources': reverse('resources', args=[s]), 'learning': reverse('learning', args=[s]),
            'toolbox_library': reverse('toolbox_library', args=[s]), 'claims': reverse('claims', args=[s]),
        }

    def snapshot(self):
        return {model.__name__: model.objects.count() for model in WATCHED} | {
            'answers': list(Response.objects.values_list('code', flat=True)), 'event': Kaizen.objects.values_list('revision', 'status').get(pk=self.event.pk),
            'coverage': Coverage.objects.values_list('accepted', flat=True).get(pk=self.coverage.pk),
            'benefit': Benefit.objects.values_list('validated', flat=True).get(pk=self.benefit.pk),
            'session': AssessmentSession.objects.values_list('availability', flat=True).get(pk=self.session.pk)}

    def post_everything(self, names):
        payload = {'code': 'Y', 'revision': 0, 'assessment_id': self.draft.pk, 'accepted': 'on', 'decision': 'Synthetic',
                   'availability': 'confirmed', 'confirm_partial': 'on', 'title': 'Synthetic', 'text': 'Synthetic', 'kind': 'return',
                   'stage': 'Plan', 'method': '5w2h', 'progress': 100, 'action': 'submit_review', 'description': 'Synthetic', 'amount': 1}
        routes = self.routes()
        return {name: self.client.post(routes[name], payload).status_code for name in names}

    def test_other_site_users_are_refused_on_every_site_route(self):
        before = self.snapshot()
        self.client.force_login(self.outsider)
        routes = self.routes()
        got = {name: self.client.get(url).status_code for name, url in routes.items()}
        posted = self.post_everything(routes)
        self.assertEqual({k: v for k, v in got.items() if v not in DENIED}, {}, 'GET allowed for another site')
        self.assertEqual({k: v for k, v in posted.items() if v not in DENIED}, {}, 'POST allowed for another site')
        self.assertEqual(self.snapshot(), before)
        # Control: the same routes open for a member, so the refusals above are about the site, not broken URLs.
        self.client.force_login(self.users['manager'])
        member = {name: self.client.get(url).status_code for name, url in routes.items()}
        self.assertGreaterEqual(sum(1 for v in member.values() if v == 200), 30, member)

    def test_roles_cannot_change_what_they_do_not_own(self):
        # Team members and sensei never answer, approve, start, configure, plan or accept evidence.
        assessment_writes = ['respond', 'approve', 'new_draft', 'question_configuration', 'sessions', 'session_detail',
                             'review_coverage', 'other_audit', 'preparation_need']
        for role in ('staff', 'coach'):
            before = self.snapshot()
            self.client.force_login(self.users[role])
            got = self.post_everything(assessment_writes)
            self.assertEqual({k: v for k, v in got.items() if v not in DENIED}, {}, role)
            self.assertEqual(self.snapshot(), before, role)
        # Team members do not write sensei feedback or validate benefits; auditors do not edit someone else's Kaizen.
        for role, names in (('staff', ['review_note', 'kaizen_review_detail', 'validate_benefit']),
                            ('assessor', ['kaizen_detail', 'kaizen_autosave', 'kaizen_add', 'kaizen_action_edit', 'task_progress', 'toolbox', 'input_profile'])):
            before = self.snapshot()
            self.client.force_login(self.users[role])
            got = self.post_everything(names)
            self.assertEqual({k: v for k, v in got.items() if v not in DENIED}, {}, role)
            self.assertEqual(self.snapshot(), before, role)
        self.client.force_login(self.users['staff'])
        self.assertIn(self.client.get(self.routes()['review_queue']).status_code, DENIED)
