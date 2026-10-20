"""Hosted demo preparation: works without private sources, sets accounts, collects feedback."""
import os
from pathlib import Path
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import A3Report, Category, DemoFeedback, Kaizen, Membership, Requirement

MISSING=(Path('does-not-exist/catalog.json'),)

@override_settings(MEDIA_ROOT='tmp/test-demo-media')
class HostedDemoTests(TestCase):
    def prepare(self,**env):
        values={'TCA_DEMO_PASSWORD':'Synthetic-demo-pass-1','TCA_TESTERS':'Anna de Boer:auditor, Ben Smit:team',**env}
        with patch.dict(os.environ,values), patch('core.management.commands.import_demo_catalog.CATALOG_FILES',MISSING), \
             patch('core.source.KAIZEN_FILES',MISSING):
            from core.source import kaizen_record
            kaizen_record.cache_clear()
            try: call_command('prepare_demo',verbosity=0)
            finally: kaizen_record.cache_clear()

    def test_prepare_without_private_sources_is_synthetic_and_repeatable(self):
        self.prepare();self.prepare()
        self.assertEqual((Category.objects.count(),Requirement.objects.count()),(15,150))
        self.assertIn('SYNTHETIC',Requirement.objects.first().detail_text)
        anna=get_user_model().objects.get(username='anna.de.boer')
        self.assertTrue(anna.check_password('Synthetic-demo-pass-1'))
        self.assertTrue(Membership.objects.filter(user=anna,role='assessor',site__code='fictional-matrix-pilot').exists())
        self.assertTrue(get_user_model().objects.get(username='team_demo').check_password('Synthetic-demo-pass-1'))
        self.assertEqual(Kaizen.objects.filter(title__startswith='FICTIONAL pre-shift').count(),1)

    def test_password_is_required(self):
        with patch.dict(os.environ,{'TCA_DEMO_PASSWORD':'short'}), self.assertRaises(CommandError): call_command('prepare_demo',verbosity=0)

    def test_feedback_saved_and_only_managers_read_it(self):
        self.prepare()
        team=get_user_model().objects.get(username='ben.smit');self.client.force_login(team)
        self.client.post(reverse('feedback_add'),{'page':'/sites/fictional-matrix-pilot/evidence/','rating':'unclear','text':'Fictional: filter label unclear'})
        self.client.post(reverse('feedback_add'),{'page':'https://evil.example/','text':'Redirect check'})
        self.assertEqual(DemoFeedback.objects.count(),2)
        self.assertEqual(DemoFeedback.objects.get(text='Redirect check').page,'/')
        self.assertEqual(self.client.get(reverse('feedback_list')).status_code,404)
        self.client.force_login(get_user_model().objects.get(username='manager_demo'))
        self.assertContains(self.client.get(reverse('feedback_list')),'filter label unclear')
        self.assertIn('Fictional: filter label unclear',self.client.get(reverse('feedback_list'),{'format':'csv'}).content.decode('utf-8-sig'))

    def test_stored_pdf_is_rebuilt_when_file_store_was_wiped(self):
        self.prepare()
        report=A3Report.objects.filter(paper='A3').first()
        report.file.storage.delete(report.file.name)
        self.client.force_login(get_user_model().objects.get(username='sensei_demo'))
        response=self.client.get(reverse('a3_download',args=[report.event.site.code,report.event_id,report.pk]))
        self.assertEqual(response.status_code,200);self.assertTrue(response.content.startswith(b'%PDF'))
