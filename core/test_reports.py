import json,zipfile
from io import BytesIO
from django.test import TestCase,override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import *
from .a3 import build_pdf,ensure_report,report_snapshot
from .toolbox_registry import initial_payload

@override_settings(MEDIA_ROOT='tmp/test-report-media')
class ReportLearningTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('report-test',password='test-password')
        self.staff=get_user_model().objects.create_user('report-staff',password='test-password')
        self.site=Site.objects.create(name='Synthetic report site',code='report-site')
        self.other=Site.objects.create(name='Synthetic learning recipient',code='report-recipient')
        for site in (self.site,self.other):
            for role in ('staff','manager','coach'):Membership.objects.create(user=self.user,site=site,role=role)
        Membership.objects.create(user=self.staff,site=self.other,role='staff')
        self.event=Kaizen.objects.create(site=self.site,title='Fictional A3 result',profile='BP',input_profile='small',created_by=self.user,local_status='closed',status='verified',data={'overall_problem':'Original long narrative '*400,'process_location':'Synthetic location','solution':'Proven synthetic approach','sustain':'Recheck locally','baseline':'10','actual':'8'})
        self.payload=initial_payload('pareto');self.payload['rows']=[{'id':'a','category':'Labels','value':30,'unit':'count','source':'Synthetic'},{'id':'b','category':'Damage','value':20,'unit':'count','source':'Synthetic'}];self.payload['conclusion']='Test a label-position change; local proof needed.'
        Worksheet.objects.create(event=self.event,method='pareto',stage='Check',title='Synthetic Pareto',payload=self.payload)
        self.client.force_login(self.user)

    def test_pdf_versions_long_text_full_archive_and_privacy(self):
        from pypdf import PdfReader
        report=ensure_report(self.event,self.user)
        raw=report.file.read();report.file.close();reader=PdfReader(BytesIO(raw))
        self.assertGreaterEqual(len(reader.pages),2)
        self.assertAlmostEqual(float(reader.pages[0].mediabox.width),1190.551,places=2)
        self.assertIn('Summary shortened',''.join(p.extract_text() for p in reader.pages))
        self.assertEqual(report.snapshot['data']['overall_problem'],self.event.data['overall_problem'])
        self.assertEqual(ensure_report(self.event,self.user).pk,report.pk)
        self.event.revision=1;self.event.data['solution']='Changed outcome requires new review';self.event.save()
        next_report=ensure_report(self.event,self.user);self.assertEqual(next_report.version,2)
        report.refresh_from_db();self.assertEqual(report.snapshot['data']['solution'],'Proven synthetic approach')
        response=self.client.get(reverse('event_archive_zip',args=[self.site.code,self.event.pk]))
        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            complete=json.loads(archive.read('event-complete.json'));self.assertEqual(complete['data']['overall_problem'],self.event.data['overall_problem']);self.assertEqual(complete['worksheets'][0]['payload']['rows'],self.payload['rows'])
            self.assertIn('reports/a3-v1.pdf',archive.namelist())
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('a3_download',args=[self.site.code,self.event.pk,report.pk])).status_code,404)

    def test_explicit_sharing_scope_and_adaptation_no_local_approval_inheritance(self):
        ensure_report(self.event,self.user)
        url=reverse('learning_publish',args=[self.site.code,self.event.pk])
        response=self.client.post(url,{'revision':0,'context':'Fictional packaging context','transfer_limits':'Validate local equipment and safety independently.','allowed_sites':[self.other.pk],'approval_reason':'Synthetic pilot sharing only'})
        self.assertEqual(response.status_code,302,response.content)
        entry=LearningEntry.objects.get();self.assertNotIn('baseline',entry.approach['data'])
        self.assertContains(self.client.get(reverse('learning',args=[self.site.code])),'No learning entries')
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse('learning',args=[self.other.code])),'Fictional A3 result')
        response=self.client.post(reverse('learning_adapt',args=[self.other.code,entry.pk]),{'title':'New local fictional issue'})
        self.assertEqual(response.status_code,302);draft=Kaizen.objects.latest('pk')
        self.assertEqual((draft.status,draft.local_status),('proposed','open'))
        self.assertEqual(draft.profile,'A4');self.assertFalse(draft.linked_requirements.exists());self.assertFalse(draft.observations.exists());self.assertFalse(draft.benefits.exists());self.assertFalse(draft.attachments.exists())
        self.assertNotIn('baseline',draft.data);self.assertNotIn('coach_review',draft.data)
        self.assertEqual(draft.worksheets.first().payload['rows'],[])

    def test_local_closure_cannot_publish_learning_or_skip_global_gates(self):
        self.event.status='proposed';self.event.save()
        url=reverse('learning_publish',args=[self.site.code,self.event.pk])
        self.assertContains(self.client.post(url,{'revision':0,'context':'Synthetic','transfer_limits':'Local validation','allowed_sites':[self.other.pk],'approval_reason':'Test'}),'sensei verification is required')
        self.assertFalse(LearningEntry.objects.exists())

    def test_five_s_photo_pdf_preview_and_current_evidence_restriction(self):
        from PIL import Image
        from django.core.files.base import ContentFile
        from pypdf import PdfReader
        raw=BytesIO();Image.new('RGB',(30,20),'blue').save(raw,format='PNG')
        attachment=EventAttachment.objects.create(event=self.event,title='Fictional before photo',stage='Check',version='1',provenance='Synthetic image fixture',original_name='synthetic.png',created_by=self.user,file=ContentFile(raw.getvalue(),name='synthetic.png'))
        payload=initial_payload('5s');payload['rows'][0].update(before_attachment=str(attachment.pk),observation='Fictional sorting gap',score='1')
        Worksheet.objects.create(event=self.event,method='5s',title='Fictional 5S',stage='Do',payload=payload)
        report=ensure_report(self.event,self.user);reader=PdfReader(BytesIO(report.file.read()));report.file.close()
        self.assertTrue(any(len(page.images)>0 for page in reader.pages))
        self.assertEqual(self.client.get(reverse('attachment_preview',args=[self.site.code,self.event.pk,attachment.pk])).status_code,200)
        evidence=Evidence.objects.create(site=self.site,title='Initially internal photo',owner='Synthetic',evidence_type='document',created_by=self.user)
        attachment.evidence=evidence;attachment.save()
        evidence.classification='financial';evidence.save()
        local_staff=get_user_model().objects.create_user('local-photo-staff',password='test-password');Membership.objects.create(user=local_staff,site=self.site,role='staff');self.client.force_login(local_staff)
        self.assertEqual(self.client.get(reverse('attachment_preview',args=[self.site.code,self.event.pk,attachment.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('a3_download',args=[self.site.code,self.event.pk,report.pk])).status_code,404)
