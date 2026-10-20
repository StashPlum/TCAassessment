"""TCA 3.3: V3 catalogue import, group resolution, site setup blocker, group mapping and evidence attach.

Uses a synthetic source extract with fictional wording only; the private workbook is never needed.
"""
import hashlib
import json
import tempfile
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from .catalogue import SiteSetupBlocker, setup_blocker, site_requirements
from .models import (Assessment, AuditEvent, CatalogueVersion, Coverage, Evidence, Membership, Requirement, Site, TCAGroup)
from .progress import scope_for
from .v3_source import COLUMNS, EXTRACT_SCHEMA, clauses, parse

GROUPS = ('SYNTH_GROUP_01', 'SYNTH_GROUP_02')
VARIANT_SECTIONS = (2, 5)  # 14 questions with one variant per group: 150 + 14 = 164 records
LEVEL = {'C': 'CERTIFIED', 'B': 'ADVANCED', 'A': 'SHOWCASE'}


def synthetic_rows(release='TCA v3 synthetic test release', tweak=None):
    """Raw rows in the workbook layout: a release row, the header, then numbered records with continuation rows."""
    rows = [[1, [release] + [None] * 10], [2, list(COLUMNS)]]
    number, order = 3, 0

    def add(qid, position, section, level, groups, text, evidence_more=None):
        nonlocal number, order
        order += 1
        lines = text.split('\n')
        rows.append([number, [order, qid, position, f'{section:02d}. Fictional section {section}', LEVEL[level], 'EN', ';'.join(groups),
                              'Ground & Rail', lines[0], f'FICTIONAL evidence {qid}', f'FICTIONAL explanation {qid}']])
        number += 1
        for i, line in enumerate(lines[1:]):
            rows.append([number, [None] * 8 + [line, evidence_more if i == 0 else None, None]]); number += 1

    for section in range(1, 16):
        for position in range(1, 11):
            level = 'C' if position <= 5 else 'B' if position <= 8 else 'A'
            qid = f'{section:02d}.{position:02d}.{level}'
            text = f'FICTIONAL intro {qid}\nA.) first part {qid}\n\nB.) second part {qid}' if position == 1 else f'FICTIONAL single {qid}'
            if section in VARIANT_SECTIONS and position <= 7:
                for n, group in enumerate(GROUPS, 1):
                    add(qid, position, section, level, [group], f'FICTIONAL variant {n} of {qid}' + ('\nFICTIONAL second line' if n == 2 else ''), evidence_more='FICTIONAL more evidence' if n == 2 else None)
            else:
                add(qid, position, section, level, list(GROUPS), text)
    if tweak: tweak(rows)
    return {'schema': EXTRACT_SCHEMA, 'filename': 'synthetic.json', 'sha256': hashlib.sha256(json.dumps(rows).encode()).hexdigest(),
            'sheet': 'Blad1', 'rows': rows}


class V3CatalogueTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def source(self, **kwargs):
        data = synthetic_rows(**kwargs)
        path = Path(self.tmp.name) / f"source-{data['sha256'][:8]}.json"
        path.write_text(json.dumps(data), encoding='utf-8')
        return str(path), data

    def run_import(self, path, *extra):
        call_command('import_v3_catalogue', '--source', path, '--allow-counts', *extra, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))

    def test_parse_keeps_continuation_rows_exactly(self):
        _, data = self.source()
        header, records, anomalies = parse(data)
        self.assertEqual((len(records), anomalies), (164, []))
        first = records[0]
        self.assertEqual(first['requirement'], 'FICTIONAL intro 01.01.C\nA.) first part 01.01.C\n\nB.) second part 01.01.C')
        intro, units = clauses(first['requirement'])
        self.assertEqual((intro, [u['label'] for u in units]), ('FICTIONAL intro 01.01.C', ['A', 'B']))
        self.assertEqual(units[0]['text'], 'A.) first part 01.01.C')  # trailing spacer line belongs to no part
        self.assertEqual(header['release'], 'TCA v3 synthetic test release')

    def test_dry_run_stores_nothing(self):
        path, _ = self.source()
        self.run_import(path, '--dry-run')
        self.assertFalse(CatalogueVersion.objects.exists())
        self.assertFalse(Requirement.objects.filter(question_id__gt='').exists())

    def test_import_is_idempotent_and_variants_resolve_per_group(self):
        path, _ = self.source()
        self.run_import(path, '--activate')
        self.run_import(path, '--activate')
        catalogue = CatalogueVersion.objects.get()
        self.assertEqual((catalogue.status, Requirement.objects.filter(catalogue=catalogue).count(), catalogue.groups.count()), ('active', 164, 2))
        one, two = (TCAGroup.objects.get(code=g) for g in GROUPS)
        for group, n in ((one, 1), (two, 2)):
            reqs = Requirement.objects.filter(catalogue=catalogue, groups=group)
            self.assertEqual((reqs.count(), reqs.values('question_id').distinct().count()), (150, 150))
            variant = reqs.get(question_id='02.03.C')
            self.assertEqual((variant.code, variant.detail_text), (f'02.03.C~{n}', f'FICTIONAL variant {n} of 02.03.C' + ('\nFICTIONAL second line' if n == 2 else '')))
        self.assertEqual(Requirement.objects.get(code='02.03.C~2').expected_evidence, 'FICTIONAL evidence 02.03.C\nFICTIONAL more evidence')
        self.assertEqual(Requirement.objects.get(code='01.01.C').clauses.count(), 2)

    def test_inconsistent_source_imports_nothing(self):
        def drop_variant(rows):
            # Remove group 02's variant of 05.01.C: group 02 then lacks a question.
            del rows[[r[1][1] for r in rows].index('05.01.C') + 1]
        path, _ = self.source(tweak=drop_variant)
        with self.assertRaises(CommandError):
            self.run_import(path)
        self.assertFalse(CatalogueVersion.objects.exists())

    def test_orphan_continuation_is_an_error(self):
        def orphan(rows): rows.insert(5, [999, [None, None, None, 'stray', None, None, None, None, 'x', None, None]])
        path, _ = self.source(tweak=orphan)
        with self.assertRaises(CommandError):
            self.run_import(path, '--dry-run')

    def test_new_version_keeps_earlier_records_and_assessments(self):
        path, _ = self.source()
        self.run_import(path, '--activate')
        group = TCAGroup.objects.get(code=GROUPS[0])
        site = Site.objects.create(code='fictional-v33-site', name='Fictional V33 Site', tca_group=group)
        user = get_user_model().objects.create_user('v33-auditor')
        old = Assessment.objects.create(site=site, version=1, created_by=user)
        old_scope = list(scope_for(old)['requirements'])
        path2, _ = self.source(release='TCA v3 synthetic test release 2')
        self.run_import(path2, '--activate')
        first, second = CatalogueVersion.objects.order_by('pk')
        self.assertEqual((first.status, second.status), ('retired', 'active'))
        self.assertTrue(Requirement.objects.filter(catalogue=second, code='02.03.C~b1').exists())
        self.assertEqual(Requirement.objects.get(code='02.03.C~1').catalogue, first)
        old.refresh_from_db()
        self.assertEqual(scope_for(old)['requirements'], old_scope)
        # Site is mapped to a group of the retired version: blocked until re-mapped, never defaulted.
        self.assertTrue(setup_blocker(site))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='tca-v33-media-'))
class V3SiteSetupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        data = synthetic_rows()
        cls.dir = tempfile.mkdtemp(prefix='tca-v33-src-')
        path = Path(cls.dir) / 'synthetic.json'
        path.write_text(json.dumps(data), encoding='utf-8')
        call_command('import_v3_catalogue', '--source', str(path), '--allow-counts', '--activate', stdout=open('/dev/null', 'w'))
        User = get_user_model()
        cls.site = Site.objects.create(code='fictional-v33-unmapped', name='Fictional Unmapped Site')
        cls.admin, cls.auditor, cls.staff, cls.outsider = (User.objects.create_user(n) for n in ('v33-admin', 'v33-aud', 'v33-staff', 'v33-out'))
        for user, role in ((cls.admin, 'admin'), (cls.auditor, 'assessor'), (cls.staff, 'staff')):
            Membership.objects.create(user=user, site=cls.site, role=role)
        cls.other = Site.objects.create(code='fictional-v33-other', name='Fictional Other Site')
        Membership.objects.create(user=cls.outsider, site=cls.other, role='admin')

    def test_unmapped_site_is_blocked_not_defaulted(self):
        with self.assertRaises(SiteSetupBlocker):
            site_requirements(self.site)
        self.client.force_login(self.auditor)
        self.client.post(reverse('new_draft', args=[self.site.code]))
        self.assertFalse(self.site.assessments.exists())

    def test_group_mapping_needs_admin_preview_and_confirmation(self):
        url = reverse('site_group_map', args=[self.site.code])
        for user in (self.auditor, self.staff, self.outsider):
            self.client.force_login(user)
            self.assertEqual(self.client.post(url, {'group': GROUPS[1], 'confirm': 'yes'}).status_code, 404)
        self.client.force_login(self.admin)
        preview = self.client.get(url, {'group': GROUPS[1]})
        self.assertContains(preview, '150')
        self.client.post(url, {'group': GROUPS[1]})
        self.site.refresh_from_db()
        self.assertIsNone(self.site.tca_group)
        self.client.post(url, {'group': GROUPS[1], 'confirm': 'yes'})
        self.site.refresh_from_db()
        self.assertEqual(self.site.tca_group.code, GROUPS[1])
        self.assertTrue(AuditEvent.objects.filter(action='tca_group_mapped', site=self.site).exists())
        self.client.force_login(self.auditor)
        self.client.post(reverse('new_draft', args=[self.site.code]))
        draft = self.site.assessments.get()
        codes = scope_for(draft)['requirements']
        self.assertEqual((len(codes), '02.03.C~2' in codes, '02.03.C~1' in codes), (150, True, False))

    def test_attach_evidence_permissions_and_rules(self):
        self.site.tca_group = TCAGroup.objects.get(code=GROUPS[0]); self.site.save()
        draft = Assessment.objects.create(site=self.site, version=1, created_by=self.auditor)
        url = reverse('attach_evidence', args=[self.site.code, '01.01.C'])
        item = Evidence.objects.create(site=self.site, title='FICTIONAL board photo', evidence_type='document', owner='x', created_by=self.auditor)
        self.client.force_login(self.staff)
        self.assertIn(self.client.post(url, {'assessment_id': draft.pk, 'existing': item.pk}).status_code, (403, 404))
        self.client.force_login(self.outsider)
        self.assertIn(self.client.post(url, {'assessment_id': draft.pk, 'existing': item.pk}).status_code, (403, 404))
        self.assertFalse(Coverage.objects.exists())
        self.client.force_login(self.auditor)
        self.client.post(url, {'assessment_id': draft.pk, 'existing': item.pk, 'accept': 'on'})  # accept without reason
        self.assertFalse(Coverage.objects.exists())
        bad = self.client.post(url, {'assessment_id': draft.pk, 'existing': item.pk, 'next': 'https://example.invalid/'})
        self.assertTrue(bad['Location'].startswith(f'/sites/{self.site.code}/assessment/'))
        self.assertEqual(Coverage.objects.filter(evidence=item).count(), 2)
        self.assertFalse(Coverage.objects.filter(accepted=True).exists())
        # A variant of the other group is outside this assessment's scope.
        self.client.post(reverse('attach_evidence', args=[self.site.code, '02.03.C~2']), {'assessment_id': draft.pk, 'existing': item.pk})
        self.assertEqual(Coverage.objects.filter(evidence=item).count(), 2)
