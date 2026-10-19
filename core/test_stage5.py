"""Stage 5: learning by requirement, best practice, evidence library, reports and the full role journey."""
from datetime import date, timedelta
from io import BytesIO
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import (A3Report, Assessment, BestPracticeValidation, Coverage, Evidence, EventAttachment, Kaizen, KaizenAction,
                     LearningEntry, Membership, Observation, Participant, Requirement, Response, Site)
from .progress import coverage_progress

@override_settings(MEDIA_ROOT='tmp/test-stage5-media')
class StageFiveJourneyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_catalog',verbosity=0)
        call_command('seed_stage1_demo',verbosity=0)
        call_command('seed_stage2_demo',verbosity=0)
        User=get_user_model()
        cls.users={name:User.objects.get(username=name) for name in ('auditor_demo','manager_demo','sensei_demo','team_demo')}
        cls.matrix=Site.objects.get(code='fictional-matrix-pilot')
        cls.recipient=Site.objects.get(code='fictional-stage-one')
        cls.outsider=User.objects.create_user('s5-outsider')
        cls.private=Site.objects.create(code='fictional-s5-private',name='Fictional Private Site')
        Membership.objects.create(user=cls.outsider,site=cls.private,role='staff')
        Membership.objects.get_or_create(user=cls.users['manager_demo'],site=cls.recipient,role='manager')

    def login(self,name): self.client.force_login(self.users[name])

    def test_counter_check_56_y_19_advisory_75_n(self):
        progress=coverage_progress(self.matrix)
        self.assertEqual((progress['assessed']['count'],progress['assessed']['total']),(150,150))
        self.assertEqual((progress['coverage']['count'],progress['coverage']['total']),(75,150))
        self.assertEqual(progress['open_advisory_count'],19)
        codes=list(self.matrix.assessments.first().responses.values_list('code',flat=True))
        self.assertEqual((codes.count('Y'),codes.count('A'),codes.count('N')),(56,19,75))
        self.login('manager_demo')
        self.client.post(reverse('switch_site'),{'site_code':self.matrix.code,'area':'home'})
        page=self.client.get(reverse('home'))
        self.assertContains(page,'150/150');self.assertContains(page,'CAT confirmation pending')
        # Reports list the same frozen numbers, with Advisory separate from N.
        report=self.client.get(reverse('resources',args=[self.matrix.code]),{'type':'asm'})
        self.assertIn(['v1','Approved','advisory-v2'],[row[:3] for row in report.context['rows']])
        self.assertEqual(report.context['rows'][0][7:10],[56,19,75])

    def test_full_journey_kaizen_review_learning_and_adoption(self):
        site=self.matrix
        requirement=Requirement.objects.get(code='4.C.3')
        # Auditor: requirement detail links to Kaizen start, learnings and evidence for the same ID.
        self.login('auditor_demo')
        detail=self.client.get(reverse('respond',args=[site.code,'4.C.3']))
        for text in ('Start Kaizen','Learnings for 4.C.3','Evidence for 4.C.3'): self.assertContains(detail,text)
        history=self.client.get(reverse('assessment_history',args=[site.code]))
        self.assertEqual(history.status_code,200)
        # Team member starts a Kaizen from the requirement, assigns a task and submits.
        self.login('team_demo')
        self.client.post(reverse('kaizens',args=[site.code]),{'title':'Fictional journey pre-shift meeting','requirement':'4.C.3','profile':'A4'})
        event=Kaizen.objects.get(title='Fictional journey pre-shift meeting')
        self.assertEqual(list(event.linked_requirements.all()),[requirement])
        event.data.update(specific_problem='Synthetic skipped meetings',solution='Synthetic fixed slot',baseline='60',actual='96',unit='%',
                          population='Synthetic shifts',data_source='Synthetic board',sustain='Synthetic weekly check',root_cause='Synthetic no agenda')
        event.save()
        lead=event.participants.get(kaizen_role='Kaizen lead')
        for phase in ('DO','ACT'):
            KaizenAction.objects.create(event=event,phase=phase,description=f'Synthetic {phase}',owner='team_demo',assignee=lead,start_date=date(2026,10,1),end_date=date(2026,10,20),progress=100)
        for phase,value in [('before',60),('after',96)]:
            Observation.objects.create(event=event,phase=phase,measure='Meetings held',value=value,unit='%',population='Synthetic shifts',period_start=date(2026,9,1),period_end=date(2026,9,2),data_source='Synthetic board')
        self.assertContains(self.client.get(reverse('kaizen_detail',args=[site.code,event.pk]),{'view':'gantt'}),'Synthetic DO')
        self.client.post(reverse('kaizen_detail',args=[site.code,event.pk]),{'revision':event.revision,'action':'submit_review'})
        event.refresh_from_db();self.assertEqual(event.status,'results_under_review')
        # Sensei finalises; A3 and A4 are stored and the TCA answer is unchanged.
        before=Response.objects.get(assessment=site.assessments.first(),requirement=requirement).code
        self.login('sensei_demo')
        self.client.post(reverse('kaizen_review_detail',args=[site.code,event.pk]),{'revision':event.revision,'decision':'finalize','coach_review':'Synthetic sensei review'})
        event.refresh_from_db();self.assertEqual(event.status,'verified')
        report=event.a3_reports.get(paper='A3',event_revision=event.revision)
        self.assertEqual(self.client.get(reverse('a3_download',args=[site.code,event.pk,report.pk])).status_code,200)
        self.assertEqual(Response.objects.get(assessment=site.assessments.first(),requirement=requirement).code,before)
        # Manager shares the learning with another site.
        self.login('manager_demo')
        self.client.post(reverse('learning_publish',args=[site.code,event.pk]),{'revision':event.revision,'context':'Synthetic hall context',
            'transfer_limits':'Check local shift pattern.','allowed_sites':[self.recipient.pk],'approval_reason':'Synthetic pilot sharing'})
        entry=LearningEntry.objects.get(event=event)
        # Team member at the other site finds it by the exact requirement ID.
        self.login('team_demo')
        page=self.client.get(reverse('learning',args=[self.recipient.code]),{'req':'4.C.3'})
        card=page.context['selected']
        self.assertEqual(card['entry'],entry);self.assertEqual(card['codes'],['4.C.3'])
        self.assertEqual((card['comparison']['before'],card['comparison']['after']),(60.0,96.0))
        self.assertContains(page,'Not validated as best practice')
        self.assertEqual(len(self.client.get(reverse('learning',args=[self.recipient.code]),{'req':'1.C.1'}).context['cards']),0)
        # Only the TCA auditor validates best practice; team members and the sensei cannot.
        self.assertEqual(self.client.post(reverse('best_practice_validate',args=[self.recipient.code,entry.pk]),{'how_achieved':'x'*12,'validation_basis':'y'*12}).status_code,404)
        self.login('sensei_demo')
        url=reverse('best_practice_validate',args=[self.recipient.code,entry.pk])
        self.assertEqual(self.client.post(url,{'how_achieved':'x'*12,'validation_basis':'y'*12}).status_code,404)
        self.login('auditor_demo')
        self.client.post(url,{'how_achieved':'short','validation_basis':'short'})
        self.assertFalse(BestPracticeValidation.objects.exists())
        self.client.post(url,{'how_achieved':'Fixed slot sustained for three months','validation_basis':'Synthetic board data at two sites'})
        practice=BestPracticeValidation.objects.get();self.assertEqual(practice.validated_by,self.users['auditor_demo'])
        page=self.client.get(reverse('learning',args=[self.recipient.code]),{'practice':'validated'})
        self.assertContains(page,'Validated by');self.assertEqual(len(page.context['cards']),1)
        # Adoption creates a new linked draft without approvals, evidence, measures or TCA answers.
        self.login('team_demo')
        self.client.post(reverse('learning_adapt',args=[self.recipient.code,entry.pk]),{'title':'Fictional adopted meeting'})
        draft=Kaizen.objects.get(title='Fictional adopted meeting')
        self.assertEqual((draft.site,draft.status,draft.data['adapted_from_learning']),(self.recipient,'proposed',entry.pk))
        self.assertFalse(draft.observations.exists() or draft.attachments.exists() or draft.a3_reports.exists() or draft.benefits.exists())
        self.assertNotIn('coach_review',draft.data);self.assertFalse(draft.linked_requirements.exists())
        # The source event is not opened for users without access to its site.
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(reverse('learning',args=[self.recipient.code])).status_code,404)

    def test_evidence_library_filters_reuse_without_duplicates_and_export_scope(self):
        site=self.matrix
        self.login('auditor_demo')
        item=Evidence.objects.create(site=site,title='Fictional board photo',evidence_type='observation',owner='Fictional owner',created_by=self.users['auditor_demo'],
                                     valid_until=timezone.localdate()+timedelta(days=90),period_start=date(2026,10,1),period_end=date(2026,10,7))
        expired=Evidence.objects.create(site=site,title='Fictional expired minutes',evidence_type='document',owner='Other owner',created_by=self.users['auditor_demo'],valid_until=date(2026,1,1))
        Evidence.objects.create(site=site,title='Fictional HR file',evidence_type='document',owner='HR',classification='hr',created_by=self.users['auditor_demo'])
        event=Kaizen.objects.filter(site=site).first()
        EventAttachment.objects.create(event=event,stage='Check',evidence=item,title='Linked photo',version='1',provenance='Existing evidence',created_by=self.users['auditor_demo'])
        url=reverse('evidence',args=[site.code])
        link=reverse('evidence_link_requirement',args=[site.code,item.pk])
        self.client.post(link,{'requirement_code':'4.C.3'})
        clauses=Requirement.objects.get(code='4.C.3').clauses.count()
        self.assertEqual(Coverage.objects.filter(evidence=item).count(),clauses)
        response=self.client.post(link,{'requirement_code':'4.C.3'},follow=True)
        self.assertContains(response,'No duplicate link or upload was created')
        self.assertEqual(Coverage.objects.filter(evidence=item).count(),clauses);self.assertEqual(Evidence.objects.filter(title='Fictional board photo').count(),1)
        page=self.client.get(url,{'req':'4.C.3'})
        rows=page.context['rows'];self.assertEqual([r['item'] for r in rows],[item])
        self.assertEqual(rows[0]['events'],[event]);self.assertEqual(rows[0]['status'],'review')
        self.assertEqual([r['item'] for r in self.client.get(url,{'status':'expired'}).context['rows']],[expired])
        self.assertEqual([r['item'] for r in self.client.get(url,{'owner':'Fictional owner','from':'2026-10-05','to':'2026-10-06'}).context['rows']],[item])
        csv=self.client.get(url,{'req':'4.C.3','format':'csv'}).content.decode('utf-8-sig').splitlines()
        self.assertEqual(len(csv),2);self.assertIn(f'EV-{item.pk}',csv[1])
        # Team members never see or export restricted evidence; other sites are refused.
        self.login('team_demo')
        titles=[r['item'].title for r in self.client.get(url).context['rows']]
        self.assertNotIn('Fictional HR file',titles)
        self.assertNotIn('Fictional HR file',self.client.get(url,{'format':'csv'}).content.decode())
        self.assertEqual(self.client.post(link,{'requirement_code':'1.C.1'}).status_code,404)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(url,{'format':'csv'}).status_code,404)

    def test_reports_show_relevant_filters_reset_empty_state_and_export_scope(self):
        site=self.matrix;self.login('manager_demo')
        url=reverse('resources',args=[site.code])
        kaizens=self.client.get(url,{'type':'kz'})
        self.assertEqual([f['key'] for f in kaizens.context['primary_filters']],['state','method','req'])
        self.assertEqual([f['key'] for f in kaizens.context['more_filters']],['size','year'])
        self.assertNotIn('auditor',[f['key'] for f in kaizens.context['primary_filters']+kaizens.context['more_filters']])
        empty=self.client.get(url,{'type':'kz','method':'BP'})
        self.assertContains(empty,'No rows match these filters');self.assertContains(empty,'Export scope: <strong>0</strong>',html=False)
        invalid=self.client.get(url,{'type':'asm','status':'bogus','year':'abc'})
        self.assertEqual(invalid.context['active_filters'],[])
        csv=self.client.get(url,{'type':'asm','status':'approved','format':'csv'}).content.decode('utf-8-sig').splitlines()
        self.assertEqual(len(csv),2)
        guidance=self.client.get(url,{'type':'guide','kind':'governance'})
        self.assertEqual(len(guidance.context['rows']),1)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(url,{'type':'asm','format':'csv'}).status_code,404)
