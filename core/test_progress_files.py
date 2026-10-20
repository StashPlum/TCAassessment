import hashlib,json
from io import BytesIO
from datetime import date,timedelta
from django.test import TestCase,override_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from .models import *
from .progress import coverage_progress
from .readiness import assessment_snapshot
from .files import checked_upload,read_table

@override_settings(MEDIA_ROOT='tmp/test-private-media')
class ProgressFileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_catalog',verbosity=0)
        cls.user=get_user_model().objects.create_user('toolbox-reviewer',password='local-test-password')
        cls.staff=get_user_model().objects.create_user('toolbox-staff',password='local-test-password')
        cls.site=Site.objects.create(name='Synthetic toolbox test site',code='toolbox-site')
        cls.other=Site.objects.create(name='Synthetic other site',code='toolbox-other')
        for role in ('staff','assessor','coach','manager'): Membership.objects.create(user=cls.user,site=cls.site,role=role)
        Membership.objects.create(user=cls.staff,site=cls.site,role='staff')
        cls.requirements=list(Requirement.objects.all())
        cls.evidence=Evidence.objects.create(site=cls.site,title='Synthetic current clause evidence',owner='Synthetic owner',evidence_type='document',created_by=cls.user)
        Coverage.objects.bulk_create([Coverage(evidence=cls.evidence,clause=c,accepted=True,decision='Synthetic reviewed evidence',reviewed_by=cls.user,reviewed_at=timezone.now()) for c in Clause.objects.all()])
        cls.baseline=Assessment.objects.create(site=cls.site,version=1,created_by=cls.user)
        Response.objects.bulk_create([Response(assessment=cls.baseline,requirement=r,code='Y',conclusion='Synthetic reviewed baseline',updated_by=cls.user) for r in cls.requirements[:45]])
        cls.baseline.status='approved';cls.baseline.approved_by=cls.user;cls.baseline.approved_at=timezone.now();cls.baseline.snapshot=assessment_snapshot(cls.site,cls.baseline);cls.baseline.save()
        cls.event=Kaizen.objects.create(site=cls.site,title='Synthetic import event',profile='BP',input_profile='extensive',created_by=cls.user)

    def setUp(self): self.client.force_login(self.user)

    def test_45_pending_duplicate_events_and_six_unique_acceptances(self):
        original=json.dumps(self.baseline.snapshot,sort_keys=True)
        self.assertEqual(coverage_progress(self.site)['coverage'],{'count':45,'total':150,'percent':30})
        claims=[]
        for r in self.requirements[45:51]:
            claim=VerificationClaim.objects.create(site=self.site,requirement=r,event=self.event,statement='Ready with evidence',created_by=self.staff);claim.evidence.add(self.evidence);claims.append(claim)
            self.event.linked_requirements.add(r)
        duplicate=VerificationClaim.objects.create(site=self.site,requirement=self.requirements[45],event=self.event,statement='Duplicate link',created_by=self.staff);duplicate.evidence.add(self.evidence)
        self.event.local_status='closed';self.event.status='verified';self.event.save()
        progress=coverage_progress(self.site);self.assertEqual(progress['coverage']['percent'],30);self.assertEqual(progress['pending_count'],6)
        for claim in claims:
            response=self.client.post(reverse('claim_review',args=[self.site.code,claim.pk]),{'revision':0,'decision':'accepted','reason':'Synthetic complete clause-level targeted acceptance'})
            self.assertEqual(response.status_code,302,response.content)
        progress=coverage_progress(self.site);self.assertEqual(progress['coverage'],{'count':51,'total':150,'percent':34})
        self.assertEqual(progress['pending_count'],0)
        self.baseline.refresh_from_db();self.assertEqual(json.dumps(self.baseline.snapshot,sort_keys=True),original)
        self.assertFalse(self.site.assessments.filter(full_section_review=True).exists())
        self.assertEqual(self.site.assessments.count(),7)
        self.client.post(reverse('claim_review',args=[self.site.code,duplicate.pk]),{'revision':0,'decision':'accepted','reason':'Duplicate acceptance does not increase coverage'})
        self.assertEqual(coverage_progress(self.site)['coverage']['count'],51)
        self.assertContains(self.client.get(reverse('site',args=[self.site.code])),'34%')

    def test_unknown_zero_scope_expiry_template_change_and_role_denial(self):
        self.evidence.valid_until=timezone.localdate()-timedelta(days=1);self.evidence.save()
        self.assertEqual(coverage_progress(self.site)['coverage']['count'],0)
        self.assertEqual(coverage_progress(self.site)['baseline_coverage']['count'],45)
        ApplicabilityException.objects.create(site=self.site,requirement=self.requirements[0],justification='Unapproved arithmetic',scope='local',source_authority='Pending')
        self.assertIsNone(coverage_progress(self.site)['coverage']['percent'])
        ApplicabilityException.objects.all().delete()
        new=Assessment.objects.create(site=self.site,version=2,created_by=self.user,scope_snapshot={'version':'synthetic-other-template','requirements':[],'known':True})
        progress=coverage_progress(self.site);self.assertEqual(progress['coverage']['total'],0);self.assertIsNone(progress['coverage']['percent']);self.assertFalse(progress['comparable'])
        claim=VerificationClaim.objects.create(site=self.site,requirement=self.requirements[0],statement='Test',created_by=self.staff)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('claim_review',args=[self.site.code,claim.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('site',args=[self.other.code])).status_code,404)

    def upload(self,name,raw,classification='internal'):
        self.event.refresh_from_db()
        response=self.client.post(reverse('attachment_add',args=[self.site.code,self.event.pk]),{'revision':self.event.revision,'stage':'Check','title':'Synthetic measurement file','version':'1','provenance':'Fictional fixture','classification':classification,'file':SimpleUploadedFile(name,raw)})
        self.assertEqual(response.status_code,302,response.content)
        return EventAttachment.objects.latest('pk')

    def test_private_upload_csv_import_preview_errors_confirmation_and_replay(self):
        raw=b'phase,measure,value,unit,population,date,source\nbefore,Pick time,10,min,Shift,2026-10-01,Fictional\nafter,Pick time,8,min,Shift,2026-10-02,Fictional\n'
        item=self.upload('synthetic-measures.csv',raw)
        self.assertEqual(item.sha256,hashlib.sha256(raw).hexdigest());self.assertEqual(item.file.read(),raw);item.file.close()
        self.assertEqual(self.event.observations.count(),0)
        response=self.client.post(reverse('import_preview',args=[self.site.code,self.event.pk]),{'attachment':item.pk,'sheet':''});self.assertEqual(response.status_code,302)
        preview=ImportPreview.objects.latest('pk');self.assertEqual(preview.table['rows'][0][2],'10')
        self.event.refresh_from_db();mapping={'revision':self.event.revision,'target':'observations'}
        for key,col in [('phase',0),('measure',1),('value',2),('unit',3),('population',4),('period_start',5),('period_end',5),('data_source',6)]: mapping['column_'+key]=str(col)
        mapping['column_value']='0';url=reverse('import_confirm',args=[self.site.code,self.event.pk,preview.pk])
        self.assertContains(self.client.post(url,mapping),'Source row 2');self.assertEqual(self.event.observations.count(),0)
        mapping['column_value']='2';self.assertEqual(self.client.post(url,mapping).status_code,302)
        self.assertEqual(self.event.observations.count(),2);self.event.refresh_from_db();self.assertEqual(self.event.data['baseline'],'10.0000')
        self.assertContains(self.client.post(url,mapping),'already confirmed');self.assertEqual(self.event.observations.count(),2)
        private=self.upload('restricted.csv',b'key,value\na,1\n','financial')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('attachment_download',args=[self.site.code,self.event.pk,private.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('attachment_download',args=[self.other.code,self.event.pk,item.pk])).status_code,404)

    def test_xlsx_mapping_to_pareto_and_type_rejection(self):
        from openpyxl import Workbook
        wb=Workbook();ws=wb.active;ws.title='Fictional data';ws.append(['category','count']);ws.append(['Labels',30]);ws.append(['Damage',20]);out=BytesIO();wb.save(out)
        item=self.upload('synthetic-pareto.xlsx',out.getvalue());table=read_table(item,'Fictional data');self.assertEqual(table['rows'][0],['Labels','30'])
        preview=ImportPreview.objects.create(event=self.event,attachment=item,table=table,created_by=self.user)
        self.event.refresh_from_db();url=reverse('import_confirm',args=[self.site.code,self.event.pk,preview.pk])
        response=self.client.post(url,{'target':'pareto','revision':self.event.revision,'column_category':'0','column_value':'1','constant_unit':'count','constant_source':'Fictional Excel fixture','meta_metric':'frequency','meta_unit':'count','meta_aggregation':'sum'})
        self.assertEqual(response.status_code,302,response.content);w=Worksheet.objects.get(event=self.event,method='pareto');self.assertEqual(w.payload['import_origin']['sha256'],item.sha256)
        self.assertEqual(len(w.payload['rows']),2)
        for name,raw in [('fake.pdf',b'<html>'),('fake.png',b'bad'),('bad.csv',b'\xff\x00'),('bad.xlsx',b'not zip')]:
            with self.assertRaises(Exception): checked_upload(SimpleUploadedFile(name,raw))
