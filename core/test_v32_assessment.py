"""TCA Progress 3.2 phase 2: draft answers, no carry-over, approval completeness, Focus/Section/All views."""
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Assessment, Coverage, Evidence, Membership, Requirement, Response, Site
from .progress import coverage_progress


class V32AssessmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_catalog', verbosity=0)
        cls.site = Site.objects.create(name='Synthetic 3.2 Site', code='v32-site')
        cls.other = Site.objects.create(name='Synthetic 3.2 Other', code='v32-other')
        User = get_user_model()
        cls.auditor = User.objects.create_user('v32-auditor')
        cls.manager = User.objects.create_user('v32-manager')
        cls.team = User.objects.create_user('v32-team')
        cls.outsider = User.objects.create_user('v32-outsider')
        for user, role in [(cls.auditor, 'assessor'), (cls.manager, 'manager'), (cls.team, 'staff')]:
            Membership.objects.create(user=user, site=cls.site, role=role)
        Membership.objects.create(user=cls.outsider, site=cls.other, role='assessor')
        cls.req = Requirement.objects.get(pk='1.C.1')
        cls.req2 = Requirement.objects.get(pk='1.C.2')

    def respond(self, req, assessment, **data):
        data.setdefault('assessment_id', assessment.pk)
        data.setdefault('autosave', '1')
        assessment.refresh_from_db()
        data.setdefault('revision', assessment.revision)
        return self.client.post(reverse('respond', args=[self.site.code, req.code]), data)

    def accept_evidence(self, req):
        evidence = Evidence.objects.create(site=self.site, title=f'Synthetic evidence {req.code}', evidence_type='document', owner='Fixture', created_by=self.auditor)
        for clause in req.clauses.all():
            Coverage.objects.create(evidence=evidence, clause=clause, accepted=True, reviewed_by=self.auditor, reviewed_at=timezone.now())

    def start(self):
        self.client.force_login(self.auditor)
        self.client.post(reverse('new_draft', args=[self.site.code]), {})
        return self.site.assessments.get(status='draft')

    def errors(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def test_reading_never_creates_and_start_is_one_click(self):
        for user, text in [(self.auditor, 'Start assessment'), (self.team, 'A TCA auditor starts the assessment')]:
            self.client.force_login(user)
            page = self.client.get(reverse('assessment', args=[self.site.code]))
            self.assertContains(page, text)
        self.assertFalse(Assessment.objects.filter(site=self.site).exists())
        self.client.force_login(self.team)
        self.assertEqual(self.client.post(reverse('new_draft', args=[self.site.code]), {}).status_code, 404)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(reverse('assessment', args=[self.site.code])).status_code, 404)
        draft = self.start()
        self.assertEqual(draft.version, 1)
        focus = self.client.get(reverse('assessment', args=[self.site.code]))
        self.assertEqual(focus.context['view'], 'single')
        self.assertEqual(focus.context['page'].object_list[0].code, '1.C.1')

    def test_draft_saves_any_answer_with_one_selection_and_counts_only_complete_passes(self):
        draft = self.start()
        saved = self.respond(self.req, draft, code='Y')
        self.assertEqual(saved.status_code, 200, saved.content)
        self.assertTrue(saved.json()['saved'])
        self.assertEqual(Response.objects.get(assessment=draft, requirement=self.req).code, 'Y')
        progress = coverage_progress(self.site)
        self.assertEqual(progress['assessed']['count'], 1)
        self.assertEqual(progress['coverage']['count'], 0)  # Y without conclusion/evidence is not a pass
        self.assertEqual(self.respond(self.req2, draft, code='A').status_code, 200)
        self.assertEqual(self.respond(self.req2, draft, code='').status_code, 200)
        self.assertEqual(Response.objects.get(assessment=draft, requirement=self.req2).code, '')
        # Focus view resumes at the first unanswered question.
        focus = self.client.get(reverse('assessment', args=[self.site.code]))
        self.assertEqual(focus.context['page'].object_list[0].code, '1.C.2')
        # A complete Y counts as a pass.
        self.accept_evidence(self.req)
        self.respond(self.req, draft, code='Y', conclusion='Synthetic conclusion')
        self.assertEqual(coverage_progress(self.site)['coverage']['count'], 1)

    def test_compact_answer_keeps_written_text_and_stale_revision_fails(self):
        draft = self.start()
        self.respond(self.req, draft, code='A', conclusion='Written conclusion', advisory_follow_up='Next visit check')
        self.respond(self.req, draft, code='N')  # compact control posts only the code
        row = Response.objects.get(assessment=draft, requirement=self.req)
        self.assertEqual((row.code, row.conclusion, row.advisory_follow_up), ('N', 'Written conclusion', ''))
        stale = self.respond(self.req, draft, code='Y', revision=0)
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(Response.objects.get(assessment=draft, requirement=self.req).code, 'N')

    def test_approval_lists_what_is_missing_and_keeps_draft(self):
        draft = self.start()
        self.respond(self.req, draft, code='Y')
        self.respond(self.req2, draft, code='A', conclusion='Partial control')
        self.client.force_login(self.manager)
        response = self.client.post(reverse('approve', args=[self.site.code]), {'rationale': 'Synthetic'})
        messages = ' '.join(self.errors(response))
        self.assertIn('148 of 150 questions have no answer', messages)
        self.assertIn('Add a conclusion for 1.C.1', messages)
        self.assertIn('Describe the improvement and next check for Advisory 1.C.2', messages)
        self.assertIn('Link accepted, current evidence to every clause of 1.C.1, 1.C.2', messages)
        draft.refresh_from_db()
        self.assertEqual(draft.status, 'draft')
        self.client.force_login(self.auditor)
        self.accept_evidence(self.req)
        self.accept_evidence(self.req2)
        self.respond(self.req, draft, conclusion='Synthetic conclusion', code='Y')
        self.respond(self.req2, draft, code='A', conclusion='Partial control', advisory_follow_up='Retest at next visit')
        self.client.force_login(self.manager)
        self.client.post(reverse('approve', args=[self.site.code]), {'rationale': 'Synthetic', 'confirm_partial': 'on'})
        draft.refresh_from_db()
        self.assertEqual(draft.status, 'approved')
        self.assertEqual(draft.snapshot['accepted_codes']['1.C.1'], 'Y')
        self.assertEqual(draft.snapshot['accepted_codes']['1.C.2'], 'A')
        self.client.force_login(self.auditor)
        self.assertEqual(self.respond(self.req, draft, code='N').status_code, 403)

    def test_new_draft_copies_nothing_and_shows_previous_answer_as_context(self):
        first = self.start()
        self.accept_evidence(self.req)
        self.respond(self.req, first, code='A', conclusion='Earlier partial control', advisory_follow_up='Check revised standard')
        self.client.force_login(self.manager)
        self.client.post(reverse('approve', args=[self.site.code]), {'confirm_partial': 'on'})
        first.refresh_from_db()
        snapshot = first.snapshot
        second = self.start()
        self.assertEqual(second.version, 2)
        self.assertFalse(second.responses.exists())
        focus = self.client.get(reverse('assessment', args=[self.site.code]), {'view': 'single', 'page': 1})
        self.assertContains(focus, 'Last assessment (v1)')
        self.assertContains(focus, 'Check revised standard')
        self.assertContains(focus, 'The earlier answer is not copied')
        self.respond(self.req, second, code='Y', conclusion='Retested with current evidence')
        self.assertEqual(Response.objects.get(assessment=second, requirement=self.req).advisory_retest_status, 'retested')
        first.refresh_from_db()
        self.assertEqual(first.snapshot, snapshot)

    def test_three_views_edit_the_same_records(self):
        draft = self.start()
        url = reverse('assessment', args=[self.site.code])
        self.respond(self.req, draft, code='N')
        for view in ('single', 'section', 'all'):
            page = self.client.get(url, {'view': view, 'category': '1', 'page': 1})
            self.assertEqual(page.status_code, 200)
            first = page.context['page'].object_list[0]
            self.assertEqual((first.code, first.response_code), ('1.C.1', 'N'))
            self.assertContains(page, 'data-assessment-autosave')
        section = self.client.get(url, {'view': 'section', 'category': '2'})
        self.assertEqual(section.context['section'].number, 2)
        self.assertEqual(section.context['section_prev'].number, 1)
        self.assertEqual(len(section.context['page'].object_list), 10)
        self.client.force_login(self.team)
        read_only = self.client.get(url, {'view': 'all'})
        self.assertNotContains(read_only, 'data-assessment-autosave')
        self.assertEqual(self.client.post(reverse('respond', args=[self.site.code, self.req.code]), {'code': 'Y', 'revision': 0}).status_code, 404)

    def test_matrix_marks_next_level_blockers_and_picks_version_by_role(self):
        approved = Assessment.objects.create(site=self.site, version=1, created_by=self.auditor, policy_version='advisory-v2', status='approved', approved_at=timezone.now())
        # Section 1 position 1: Y with evidence passes; position 2: Y without evidence is pending and still blocks.
        self.accept_evidence(self.req)
        for req in (self.req, self.req2):
            Response.objects.create(assessment=approved, requirement=req, code='Y', conclusion='Synthetic conclusion', updated_by=self.auditor)
        draft = Assessment.objects.create(site=self.site, version=2, created_by=self.auditor, policy_version='advisory-v2')
        Response.objects.create(assessment=draft, requirement=self.req2, code='N', updated_by=self.auditor)
        url = reverse('opportunities', args=[self.site.code])
        self.client.force_login(self.manager)
        page = self.client.get(url)
        self.assertEqual((page.context['matrix_version'], page.context['matrix_assessment']), ('approved', approved))
        cells = {c['requirement'].code: c for row in page.context['matrix']['rows'] for c in row['cells'] if c['requirement']}
        self.assertFalse(cells['1.C.1']['blocker'])
        self.assertTrue(cells['1.C.2']['pending'] and cells['1.C.2']['blocker'])
        self.assertEqual(page.context['next_level'], 'Certified')
        self.assertEqual(len(page.context['next_blockers']), 74)
        self.assertContains(page, '74 requirements block Certified')
        self.assertContains(page, '1 answer is waiting for evidence')
        only = self.client.get(url, {'state': 'blocker', 'section': '1'})
        self.assertEqual([row['category'].number for row in only.context['matrix']['rows']], [1])
        pending = self.client.get(url, {'state': 'pending'})
        self.assertEqual([row['category'].number for row in pending.context['matrix']['rows']], [1])
        self.assertEqual(self.client.get(url, {'version': 'draft'}).context['matrix_assessment'], draft)
        self.client.force_login(self.auditor)
        page = self.client.get(url)
        self.assertEqual(page.context['matrix_assessment'], draft)
        self.assertContains(page, 'they count only after approval')
        # The manager start page uses the same rule as the matrix.
        self.client.force_login(self.manager)
        self.assertContains(self.client.get(reverse('home')), '74 requirements block Certified')

    def test_prepare_evidence_leads_with_what_is_missing(self):
        self.accept_evidence(self.req)
        self.client.force_login(self.manager)
        url = reverse('preparation', args=[self.site.code])
        page = self.client.get(url)
        self.assertContains(page, '149 of 150 requirements still need complete evidence')
        self.assertNotContains(page, 'name="selected"')
        missing = self.client.get(url, {'evidence': 'missing'})
        self.assertEqual(missing.context['page'].paginator.count, 149)
        complete = self.client.get(url, {'evidence': 'complete'})
        self.assertEqual([x['requirement'].code for x in complete.context['items']], ['1.C.1'])
        self.assertContains(self.client.get(url, {'select': '1'}), 'name="selected"')

    def test_history_and_planning_speak_plainly_per_role(self):
        Assessment.objects.create(site=self.site, version=1, created_by=self.auditor, policy_version='advisory-v2', status='approved', approved_at=timezone.now())
        history = reverse('assessment_history', args=[self.site.code])
        self.client.force_login(self.manager)
        page = self.client.get(history)
        self.assertContains(page, 'Y and A pass with evidence')
        self.assertContains(page, 'checked aria-label="Select Synthetic 3.2 Site version 1"')
        self.assertNotContains(page, '>Conduct assessment</a>')
        self.client.force_login(self.auditor)
        self.assertContains(self.client.get(history), '>Conduct assessment</a>')
        self.assertContains(self.client.get(reverse('sessions', args=[self.site.code])), '<details class="disclosure" open><summary>Propose a session')
