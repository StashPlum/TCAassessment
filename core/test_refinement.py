from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from .models import Assessment, Benefit, DocumentUpdate, Kaizen, KaizenAction, KaizenRevision, Membership, Observation, Opportunity, ReviewNote, Site

class RefinementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_catalog',verbosity=0)
        cls.site=Site.objects.create(code='fictional-refine',name='Fictional Refinement Site',country_code='NL')
        cls.other=Site.objects.create(code='fictional-private',name='Fictional Other Private Site',country_code='GB')
        cls.staff=get_user_model().objects.create_user('participant')
        cls.coach=get_user_model().objects.create_user('sensei')
        Membership.objects.create(user=cls.staff,site=cls.site,role='staff')
        for role in ('coach','manager'): Membership.objects.create(user=cls.coach,site=cls.site,role=role)
        cls.outsider=get_user_model().objects.create_user('other_participant')
        Membership.objects.create(user=cls.outsider,site=cls.other,role='staff')

    def create_event(self,ready=False):
        data={'owner':'participant','process_location':'Synthetic dispatch','coach_11':'Retain legacy supplemental detail'}
        if ready:
            data.update({'overall_problem':'Synthetic delay','specific_problem':'Synthetic handover','solution':'Synthetic standard',
                         'baseline':'0','actual':'1','unit':'count','population':'shifts','data_source':'Synthetic register',
                         'sustain':'Synthetic check','coach_review':'Reviewed synthetic work'})
        event=Kaizen.objects.create(site=self.site,title='Fictional test event',profile='A4',created_by=self.staff,
                                   status='results_under_review' if ready else 'proposed',data=data)
        if ready:
            for phase in ('DO','ACT'): KaizenAction.objects.create(event=event,phase=phase,description='Synthetic '+phase,owner='participant')
            for phase,value in [('before',0),('after',1)]: Observation.objects.create(event=event,phase=phase,measure='checks',value=value,unit='count',population='shifts',period_start=date(2026,10,1),period_end=date(2026,10,2),data_source='Synthetic register')
        return event

    def test_filters_validation_export_and_site_memory(self):
        self.client.force_login(self.coach)
        from .models import Requirement
        Opportunity.objects.create(site=self.site,requirement=Requirement.objects.get(pk='1.C.1'),kind='verification',problem='Synthetic',owner='Long fictional owner name',due_date=date(2026,10,20))
        url=reverse('preparation',args=[self.site.code])
        filters={'category':'1','level':'C','owner':'Long fictional','due':'2026-10-21'}
        response=self.client.get(url,filters)
        self.assertEqual(len(response.context['items']),1)
        self.assertContains(response,'selected')
        self.assertEqual(len(self.client.get(url).context['items']),1)
        csv=self.client.get(url,{**filters,'format':'csv'})
        self.assertIn('text/csv',csv['Content-Type'])
        self.assertEqual(len(csv.content.decode().splitlines())>1,True)
        invalid=self.client.get(url,{'due':'malformed','format':'csv'})
        self.assertTrue(invalid.context['filter_form'].errors)
        self.assertNotIn('text/csv',invalid['Content-Type'])
        self.assertRedirects(self.client.get(url,{'clear':'1'}),url)
        self.assertEqual(len(self.client.get(url).context['items']),150)
        self.assertEqual(self.client.get(reverse('preparation',args=[self.other.code])).status_code,404)

    def test_quick_draft_autosave_resume_conflict_and_role(self):
        self.client.force_login(self.staff)
        response=self.client.post(reverse('kaizens',args=[self.site.code]),{'title':'Fictional quick problem'})
        self.assertEqual(response.status_code,302)
        event=Kaizen.objects.get(site=self.site)
        self.assertEqual(event.data['overall_problem'],'Fictional quick problem')
        self.assertEqual(event.data['owner'],'participant')
        self.assertEqual(event.data['process_location'],self.site.name)
        url=reverse('kaizen_autosave',args=[self.site.code,event.pk])
        self.assertEqual(self.client.post(url,{'revision':0,'root_cause':'Hypothesis only','cause_status':'hypothesis'}).status_code,200)
        event.refresh_from_db();self.assertEqual(event.revision,1)
        self.assertEqual(event.data['overall_problem'],'Fictional quick problem')
        self.assertEqual(self.client.post(url,{'revision':0,'root_cause':'Overwrite'}).status_code,409)
        self.assertEqual(self.client.post(url,{'revision':1,'result_period_start':'2026-10-12','result_period_end':'2026-10-01'}).status_code,422)
        self.assertEqual(self.client.post(url,{'revision':1,'star_7':'Y'}).status_code,403)
        self.assertContains(self.client.get(reverse('kaizen_detail',args=[self.site.code,event.pk])),'Hypothesis only')
        self.assertEqual(self.client.post(reverse('kaizen_autosave',args=[self.other.code,event.pk]),{'revision':1}).status_code,404)
        self.assertEqual(self.client.get(reverse('review_queue',args=[self.site.code])).status_code,404)
        event.refresh_from_db();self.assertNotIn('star_7',event.data)
        self.assertEqual(self.client.post(url,{'revision':1,'result_period_start':'2026-10-12'}).status_code,200)
        self.assertEqual(self.client.post(url,{'revision':2,'result_period_end':'2026-10-01'}).status_code,422)

    def test_sensei_requests_reply_resolution_and_existing_verification_gate(self):
        event=self.create_event(ready=True)
        self.client.force_login(self.coach)
        note_url=reverse('review_note',args=[self.site.code,event.pk])
        self.client.post(note_url,{'revision':0,'stage':'Check','kind':'clarify','text':'Please explain sampling.'})
        event.refresh_from_db();note=event.review_notes.get()
        stale=self.client.post(note_url,{'revision':0,'stage':'Check','kind':'advice','text':'Retain stale coaching text'})
        self.assertContains(stale,'Retain stale coaching text',status_code=409)
        self.assertEqual(event.review_notes.count(),1)
        detail=reverse('kaizen_detail',args=[self.site.code,event.pk])
        self.client.post(detail,{'revision':event.revision,'action':'verify'})
        event.refresh_from_db();self.assertEqual(event.status,'results_under_review')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(note_url,{'revision':0,'resolve':note.pk}).status_code,404)
        stale=self.client.post(note_url,{'revision':0,'reply_to':note.pk,'text':'Retain stale reply text'})
        self.assertContains(stale,'Retain stale reply text',status_code=409)
        self.client.post(note_url,{'revision':event.revision,'reply_to':note.pk,'text':'Synthetic sample explanation.'})
        event.refresh_from_db();self.assertFalse(ReviewNote.objects.get(pk=note.pk).resolved)
        self.assertEqual(self.client.post(note_url,{'revision':event.revision,'resolve':note.pk}).status_code,404)
        self.client.force_login(self.coach)
        self.client.post(note_url,{'revision':event.revision,'resolve':note.pk})
        event.refresh_from_db()
        self.client.post(detail,{'revision':event.revision,'action':'verify'})
        event.refresh_from_db();self.assertEqual(event.status,'verified')
        self.assertTrue(event.history.filter(state='verified').exists())
        self.assertFalse(Assessment.objects.filter(site=self.site).exists())
        queue=self.client.get(reverse('review_queue',args=[self.site.code]),{'scope':'all'})
        self.assertContains(queue,'Fictional test event')
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.post(reverse('review_note',args=[self.other.code,event.pk]),{'revision':event.revision,'reply_to':note.pk,'text':'No access'}).status_code,404)

    def test_approved_changes_preserve_snapshot_and_require_review(self):
        event=self.create_event(ready=True)
        event.status='verified';event.save()
        self.client.force_login(self.staff)
        self.client.post(reverse('kaizen_autosave',args=[self.site.code,event.pk]),{'revision':0,'specific_problem':'Changed synthetic problem'})
        event.refresh_from_db();self.assertEqual(event.status,'results_under_review')
        original=event.history.get(revision=0)
        self.assertEqual(original.state,'verified')
        self.assertEqual(original.snapshot['data']['specific_problem'],'Synthetic handover')
        self.assertEqual(event.data['coach_11'],'Retain legacy supplemental detail')
        page=self.client.get(reverse('kaizen_detail',args=[self.site.code,event.pk]))
        self.assertContains(page,'Changed since reviewed revision 0')
        self.assertContains(page,'Specific problem')
        self.assertEqual(KaizenRevision.objects.filter(event=event,revision=0).count(),1)

    def test_edit_actions_and_permission_filtered_history_archive(self):
        event=self.create_event(ready=True)
        Benefit.objects.create(event=event,kind='savings',amount=Decimal('98765'),unit='USD')
        self.client.force_login(self.coach)
        action=event.actions.first()
        url=reverse('kaizen_action_edit',args=[self.site.code,event.pk,action.pk])
        data={'event_revision':0,'phase':action.phase,'description':'Changed action','owner':'participant','workspace_stage':'Do'}
        self.assertEqual(self.client.post(url,data).status_code,302)
        self.assertEqual(self.client.post(url,{**data,'description':'Stale attempt'}).status_code,200)
        action.refresh_from_db();self.assertEqual(action.description,'Changed action')
        event.refresh_from_db()
        self.client.force_login(self.staff)
        archive=self.client.get(reverse('kaizen_archive',args=[self.site.code,event.pk]))
        self.assertEqual(archive.json()['benefits'],'Restricted')
        self.assertNotIn('98765',archive.content.decode())
        self.assertTrue(archive.json()['history'])
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.post(reverse('kaizen_action_edit',args=[self.other.code,event.pk,action.pk]),data).status_code,404)

    def test_autosave_requires_csrf_and_review_submission_has_gates(self):
        event=self.create_event()
        csrf_client=Client(enforce_csrf_checks=True);csrf_client.force_login(self.staff)
        self.assertEqual(csrf_client.post(reverse('kaizen_autosave',args=[self.site.code,event.pk]),{'revision':0}).status_code,403)
        self.client.force_login(self.staff)
        page=self.client.post(reverse('kaizen_detail',args=[self.site.code,event.pk]),{'revision':0,'action':'submit_review'})
        self.assertContains(page,'Before submitting')
        event.refresh_from_db();self.assertEqual(event.status,'proposed')
        self.assertEqual(self.client.get(reverse('review_queue',args=[self.other.code])).status_code,404)

    def test_observations_reuse_only_empty_summary_fields(self):
        event=self.create_event()
        self.client.force_login(self.staff)
        url=reverse('kaizen_add',args=[self.site.code,event.pk,'observation'])
        data={'phase':'before','measure':'checks','value':'0','unit':'count','population':'shifts','period_start':'2026-10-01','period_end':'2026-10-02','data_source':'Synthetic'}
        self.client.post(url,{**data,'event_revision':0})
        event.refresh_from_db();self.assertEqual(event.data['baseline'],'0.0000')
        self.client.post(url,{**data,'phase':'after','value':'1','event_revision':1})
        event.refresh_from_db();self.assertEqual(event.data['actual'],'1.0000')
        self.client.post(url,{**data,'phase':'after','value':'2','event_revision':2})
        event.refresh_from_db();self.assertEqual(event.data['actual'],'1.5000')
        self.client.post(reverse('kaizen_autosave',args=[self.site.code,event.pk]),{'revision':3,'actual':'7'})
        self.client.post(url,{**data,'phase':'after','value':'3','event_revision':4})
        event.refresh_from_db();self.assertEqual(event.data['actual'],'7')
        self.assertContains(self.client.get(reverse('kaizen_detail',args=[self.site.code,event.pk])),'differs from the comparable observation average')
        self.assertEqual(event.data['coach_11'],'Retain legacy supplemental detail')

    def test_long_action_archive_is_not_silently_truncated(self):
        event=self.create_event()
        KaizenAction.objects.create(event=event,phase='DO',description='X'*32768,owner='participant')
        self.client.force_login(self.coach)
        self.assertEqual(self.client.get(reverse('kaizen_excel',args=[self.site.code,event.pk])).status_code,422)
        data=self.client.get(reverse('kaizen_archive',args=[self.site.code,event.pk])).json()
        self.assertEqual(len(data['actions'][0]['description']),32768)

    def test_star_eight_requires_different_document_types_not_case_variants(self):
        event=self.create_event(ready=True)
        for kind in ['Work Instruction',' WORK INSTRUCTION ']:
            DocumentUpdate.objects.create(event=event,document_type=kind,name='Synthetic legacy record',updated_at=date(2026,10,12))
        self.client.force_login(self.coach)
        page=self.client.post(reverse('kaizen_detail',args=[self.site.code,event.pk]),{'revision':0,'star_8':'Y','action':'verify'})
        self.assertContains(page,'Star 8 cannot be confirmed')
        event.refresh_from_db();self.assertEqual(event.status,'results_under_review')
        from .forms import DocumentUpdateForm
        self.assertFalse(DocumentUpdateForm(data={'document_type':'Fabricated type','name':'Synthetic','updated_at':'2026-10-12'}).is_valid())
