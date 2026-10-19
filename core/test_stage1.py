"""Five-stage improvement plan: first-stage policy, roles and frozen wording."""
from copy import deepcopy
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .assessment_config import frozen_configuration
from .models import Assessment,Clause,Coverage,Evidence,Kaizen,Membership,Opportunity,Requirement,Response,Site,SiteQuestionVersion
from .progress import coverage_progress
from .readiness import assessment_snapshot
from .scoring import category_result


class StageOneTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_catalog',verbosity=0)
        cls.site=Site.objects.create(name='Synthetic Stage One',code='stage-one')
        cls.other=Site.objects.create(name='Synthetic Other Stage One',code='stage-other')
        User=get_user_model()
        cls.auditor=User.objects.create_user('stage-auditor',password='local-test')
        cls.manager=User.objects.create_user('stage-manager',password='local-test')
        cls.sensei=User.objects.create_user('stage-sensei',password='local-test')
        cls.team=User.objects.create_user('stage-team',password='local-test')
        for user,role in [(cls.auditor,'assessor'),(cls.manager,'manager'),(cls.sensei,'coach'),(cls.team,'staff')]:
            Membership.objects.create(user=user,site=cls.site,role=role)
        cls.req=Requirement.objects.get(pk='1.C.1')
        cls.evidence=Evidence.objects.create(site=cls.site,title='Synthetic current evidence',evidence_type='document',owner='Fixture',created_by=cls.auditor)
        for clause in cls.req.clauses.all():
            Coverage.objects.create(evidence=cls.evidence,clause=clause,accepted=True,decision='Synthetic clause review',reviewed_by=cls.auditor,reviewed_at=timezone.now())

    def test_versioned_advisory_pass_follow_up_and_explicit_retest(self):
        self.assertEqual(category_result({i:'A' for i in range(1,6)},'advisory-v2')['earned'],'Certified')
        self.assertIsNone(category_result({i:'A' for i in range(1,6)},'draft-v1')['earned'])
        self.client.force_login(self.auditor)
        self.client.get(reverse('assessment',args=[self.site.code]))
        first=self.site.assessments.get(version=1)
        self.assertEqual(first.policy_version,'advisory-v2')
        url=reverse('respond',args=[self.site.code,self.req.code])
        invalid=self.client.post(url,{'code':'A','conclusion':'Synthetic partial control','revision':0})
        self.assertContains(invalid,'Describe the open improvement',status_code=200)
        self.assertFalse(Response.objects.filter(assessment=first).exists())
        valid=self.client.post(url,{'code':'A','conclusion':'Synthetic evidence supports an Advisory pass',
            'advisory_follow_up':'Test revised standard next visit','revision':0})
        self.assertEqual(valid.status_code,302)
        self.assertEqual(coverage_progress(self.site)['assessed']['count'],1)
        self.assertEqual(coverage_progress(self.site)['coverage']['count'],1)
        self.assertEqual(coverage_progress(self.site)['open_advisory_count'],1)
        first_row=Response.objects.get(assessment=first,requirement=self.req)
        self.assertEqual(first_row.advisory_retest_status,'due_next')
        self.client.force_login(self.manager)
        self.client.post(reverse('approve',args=[self.site.code]),{'rationale':'Synthetic dated decision'})
        first.refresh_from_db();snapshot=deepcopy(first.snapshot)
        self.assertEqual(first.snapshot['accepted_codes'][self.req.code],'A')
        self.client.force_login(self.auditor)
        approved_detail=self.client.get(url)
        self.assertContains(approved_detail,'Synthetic evidence supports an Advisory pass')
        self.assertContains(approved_detail,'Test revised standard next visit')
        self.assertContains(approved_detail,'Due at next assessment')
        self.client.post(reverse('new_draft',args=[self.site.code]),{'rationale':'Synthetic next assessment'})
        second=self.site.assessments.get(version=2)
        carried=Response.objects.get(assessment=second,requirement=self.req)
        self.assertEqual(carried.advisory_retest_status,'pending')
        self.assertEqual(coverage_progress(self.site)['coverage']['count'],0)
        no_confirm=self.client.post(url,{'code':'Y','conclusion':'Retested','revision':0})
        self.assertContains(no_confirm,'explicit retest',status_code=200)
        self.client.force_login(self.manager)
        self.client.post(reverse('approve',args=[self.site.code]),{'rationale':'Too early'})
        second.refresh_from_db();self.assertEqual(second.status,'draft')
        self.client.force_login(self.auditor)
        retested=self.client.post(url,{'code':'Y','conclusion':'Synthetic retest with accepted evidence',
            'retest_confirm':'on','revision':0})
        self.assertEqual(retested.status_code,302)
        carried.refresh_from_db();self.assertEqual(carried.advisory_retest_status,'retested')
        self.assertEqual(coverage_progress(self.site)['coverage']['count'],1)
        first.refresh_from_db();self.assertEqual(first.snapshot,snapshot)
        self.assertEqual(first_row.code,'A')

    def test_local_versions_proposals_snapshots_and_site_permissions(self):
        url=reverse('question_configuration',args=[self.site.code,self.req.code])
        self.client.force_login(self.team)
        self.assertEqual(self.client.get(url).status_code,200)
        self.assertEqual(self.client.post(url,{}).status_code,404)
        self.client.force_login(self.auditor)
        source=self.req.detail_text
        def post(version,kind,text):
            return self.client.post(url,{'kind':kind,'question_text':text,'evidence_items':'Photo\nWork instruction',
                'local_explanation':'Synthetic local context','change_reason':'Synthetic process wording','expected_version':version})
        self.assertEqual(post(0,'local_guidance','How does this site check the control?').status_code,302)
        version1=SiteQuestionVersion.objects.get(site=self.site,version=1)
        self.assertEqual(version1.diff['question_text']['before'],source)
        self.assertEqual(post(0,'local_guidance','Stale').status_code,409)
        self.assertEqual(post(1,'official_proposal','Proposed changed obligation').status_code,302)
        self.assertEqual(SiteQuestionVersion.objects.get(site=self.site,version=2).kind,'official_proposal')
        config=frozen_configuration(self.site)
        self.assertEqual(config['requirements'][self.req.code]['question_text'],'How does this site check the control?')
        started=Assessment.objects.create(site=self.site,version=1,created_by=self.auditor,configuration_snapshot=config)
        self.assertEqual(post(2,'local_guidance','What evidence shows this local control?').status_code,302)
        started.refresh_from_db()
        self.assertEqual(started.configuration_snapshot['requirements'][self.req.code]['question_text'],'How does this site check the control?')
        self.assertEqual(frozen_configuration(self.site)['requirements'][self.req.code]['question_text'],'What evidence shows this local control?')
        self.assertEqual(self.req.detail_text,source)
        version1.question_text='Tampered'
        with self.assertRaises(ValueError): version1.save()
        self.assertEqual(self.client.get(reverse('question_configuration',args=[self.other.code,self.req.code])).status_code,404)
        self.assertEqual(self.client.post(reverse('question_configuration',args=[self.other.code,self.req.code]),{}).status_code,404)

    def test_role_home_and_server_boundaries(self):
        finding=Opportunity.objects.create(site=self.site,requirement=self.req,kind='operational',problem='Synthetic label finding',owner='stage-team')
        event=Kaizen.objects.create(site=self.site,title='Synthetic team project',profile='A4',created_by=self.team)
        for user,title in [(self.auditor,'Assessment work'),(self.manager,'Site results and blockers'),
                           (self.sensei,'Sensei coaching'),(self.team,'My Kaizen work')]:
            self.client.force_login(user)
            self.assertContains(self.client.get(reverse('home')),title)
        self.client.force_login(self.team)
        start=self.client.get(reverse('kaizens',args=[self.site.code])+'?finding='+str(finding.pk))
        self.assertContains(start,'Synthetic label finding')
        self.assertEqual(self.client.post(reverse('respond',args=[self.site.code,self.req.code]),{}).status_code,404)
        self.assertEqual(self.client.get(reverse('review_queue',args=[self.site.code])).status_code,404)
        self.client.force_login(self.auditor)
        self.assertEqual(self.client.get(reverse('kaizen_archive',args=[self.site.code,event.pk])).status_code,200)
        self.assertEqual(self.client.get(reverse('question_configuration',args=[self.other.code,self.req.code])).status_code,404)

    def test_legacy_a_remains_unresolved_and_approved_snapshot_unchanged(self):
        legacy=Assessment.objects.create(site=self.site,version=1,policy_version='draft-v1',created_by=self.auditor)
        Response.objects.create(assessment=legacy,requirement=self.req,code='A',conclusion='Historical ambiguous A',updated_by=self.auditor)
        legacy.status='approved';legacy.snapshot=assessment_snapshot(self.site,legacy);legacy.save()
        original=deepcopy(legacy.snapshot)
        self.assertEqual(coverage_progress(self.site)['coverage']['count'],0)
        self.assertEqual(coverage_progress(self.site)['assessed']['count'],1)
        self.client.force_login(self.auditor)
        self.client.post(reverse('new_draft',args=[self.site.code]),{'rationale':'Apply new explicit Advisory rule'})
        new=self.site.assessments.get(version=2)
        self.assertEqual(new.policy_version,'advisory-v2')
        self.assertEqual(Response.objects.get(assessment=new,requirement=self.req).advisory_retest_status,'pending')
        legacy.refresh_from_db();self.assertEqual(legacy.snapshot,original)

    def test_word_matrix_assessed_pass_and_advisory_counts(self):
        rows=list(Requirement.objects.all())
        self.assertEqual(len(rows),150)
        assessment=Assessment.objects.create(site=self.site,version=1,created_by=self.auditor,
            configuration_snapshot=frozen_configuration(self.site))
        Response.objects.bulk_create([Response(assessment=assessment,requirement=req,
            code='Y' if index<56 else 'A' if index<75 else 'N',
            conclusion='Synthetic assessment comment',
            advisory_follow_up='Synthetic improvement remains open' if 56<=index<75 else '',
            advisory_retest_status='due_next' if 56<=index<75 else 'not_due',updated_by=self.auditor)
            for index,req in enumerate(rows)])
        passing={req.code for req in rows[:75]}
        Coverage.objects.bulk_create([Coverage(evidence=self.evidence,clause=clause,accepted=True,
            decision='Synthetic coverage',reviewed_by=self.auditor,reviewed_at=timezone.now())
            for clause in Clause.objects.filter(requirement_id__in=passing).exclude(requirement=self.req)])
        result=coverage_progress(self.site)
        self.assertEqual(result['assessed'],{'count':150,'total':150,'percent':100})
        self.assertEqual(result['coverage'],{'count':75,'total':150,'percent':50})
        self.assertEqual(result['open_advisory_count'],19)
        self.assertIsNone(result['lowest_local'])  # N blockers still determine the lowest section
