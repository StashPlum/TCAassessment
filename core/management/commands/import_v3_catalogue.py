"""Import the TCA V3 workbook (or its JSON extract) as a new catalogue version, exactly and transactionally.

    python manage.py import_v3_catalogue --source "V3assessment .xlsx" --dry-run
    python manage.py import_v3_catalogue --source "V3assessment .xlsx" --activate

A failed check imports nothing. Running it again with the same source verifies the stored records and creates no
duplicates. A different source file becomes a new version; existing versions and assessments are never changed.
"""
import json
from datetime import datetime, timezone as dt_timezone
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from core.models import CatalogueVersion, Category, Clause, Requirement, SourceVersion, TCAGroup
from core.v3_source import LEVELS, SourceError, clauses, read_and_reconcile

EXPECTED = {'records': 164, 'questions': 150, 'sections': 15, 'groups': 16}


class DryRun(Exception):
    pass


def variant_codes(records):
    """Variant key per record: the QuestionID, or QuestionID~n (n in Master Order sequence) when a QuestionID repeats."""
    seen, totals = {}, {}
    for r in records: totals[r['question_id']] = totals.get(r['question_id'], 0) + 1
    codes = {}
    for r in records:
        q = r['question_id']
        seen[q] = seen.get(q, 0) + 1
        codes[r['master_order']] = q if totals[q] == 1 else f'{q}~{seen[q]}'
    return codes


def expected_fields(record, code):
    section_number = int(record['question_id'][:2])
    return {'category_id': section_number, 'level_code': LEVELS[str(record['level']).upper()], 'position': record['order'],
            'detail_text': record['requirement'], 'expected_evidence': record['evidence'], 'reasoning': record['explanation'],
            'remote_method': '', 'question_id': record['question_id'], 'master_order': record['master_order'],
            'section_label': record['section'],
            'source_address': f"Blad1!A{record['row']}:K{record['last_row']}"}


class Command(BaseCommand):
    help = 'Import or verify the TCA V3 catalogue from the private workbook (dry-run, idempotent, all-or-nothing).'

    def add_arguments(self, parser):
        parser.add_argument('--source', required=True, help='Path to "V3assessment .xlsx" or its JSON extract.')
        parser.add_argument('--dry-run', action='store_true', help='Check and report; store nothing.')
        parser.add_argument('--activate', action='store_true', help='Make this version the catalogue for new assessments.')
        parser.add_argument('--operator', default='command line', help='Who runs the import (recorded).')
        parser.add_argument('--report', help='Write the reconciliation report (counts and IDs, no wording) to this JSON file.')
        parser.add_argument('--allow-counts', action='store_true', help='Accept counts other than 164/150/15/16 when a reviewed source differs.')

    def handle(self, *args, **options):
        try:
            source, records, report = read_and_reconcile(options['source'])
        except (SourceError, OSError, ValueError) as error:
            raise CommandError(f'Could not read the V3 source: {error}')
        counts = {'records': report['records'], 'questions': report['questions'], 'sections': report['sections'], 'groups': len(report['groups'])}
        report.update({'source_filename': source['filename'], 'sha256': source['sha256'], 'sheet': source['sheet'],
                       'operator': options['operator'], 'checked_at': datetime.now(dt_timezone.utc).isoformat(), 'counts': counts})
        if counts != EXPECTED and not options['allow_counts']:
            report['errors'].append(f'Counts {counts} differ from the expected {EXPECTED}.')
        if options['report']:
            public = {k: v for k, v in report.items() if k != 'notes'}
            with open(options['report'], 'w', encoding='utf-8') as handle: json.dump(public, handle, indent=1, default=str)
        if report['errors']:
            for error in report['errors']: self.stderr.write(error)
            raise CommandError(f"V3 source failed {len(report['errors'])} check(s); nothing was imported.")
        try:
            with transaction.atomic():
                outcome = self.store(source, records, report, options)
                if options['dry_run']: raise DryRun
        except DryRun:
            self.stdout.write(self.style.SUCCESS(f"Dry run passed: {counts['records']} source records, {counts['questions']} QuestionIDs, "
                                                 f"{counts['sections']} sections, {counts['groups']} groups; every group resolves to 150 questions. Nothing stored."))
            return
        self.stdout.write(self.style.SUCCESS(outcome))

    def store(self, source, records, report, options):
        key = 'tca-v3-' + source['sha256'][:12]
        catalogue = CatalogueVersion.objects.filter(key=key).first()
        created = catalogue is None
        if created:
            catalogue = CatalogueVersion.objects.create(key=key, label='TCA V3 (Ground & Rail)', release_label=report['release'] or '',
                source_filename=source['filename'], sha256=source['sha256'], sheet=source['sheet'], imported_by=options['operator'],
                report={k: v for k, v in report.items() if k != 'notes'})
        elif catalogue.sha256 != source['sha256']:
            raise CommandError('A catalogue with this key has a different checksum; review before importing.')
        version, _ = SourceVersion.objects.get_or_create(filename=f"{source['filename']} [{source['sha256'][:12]}]", defaults={'sha256': source['sha256']})
        if version.sha256 != source['sha256']: raise CommandError('Stored source version checksum differs.')
        groups = {code: TCAGroup.objects.get_or_create(catalogue=catalogue, code=code)[0] for code in report['groups']}
        if set(catalogue.groups.values_list('code', flat=True)) != set(groups): raise CommandError('Stored group list differs from the source.')
        names = {}
        for r in records:
            number = int(r['question_id'][:2]); names.setdefault(number, str(r['section']).split('. ', 1)[-1])
        differences = []
        for number, name in sorted(names.items()):
            category, made = Category.objects.get_or_create(number=number, defaults={'name': name, 'source_address': f"{source['sheet']}!D (section)"})
            if not made and category.name != name: differences.append({'section': number, 'stored': category.name, 'v3': name})
        codes = variant_codes(records)
        verified = 0
        for r in records:
            code = codes[r['master_order']]
            fields = expected_fields(r, code)
            raw = {'sheet': source['sheet'], 'rows': r['rows']}
            existing = Requirement.objects.filter(code=code).first()
            if existing is None:
                if not created: raise CommandError(f'{code} is missing from the stored version; the stored catalogue is incomplete.')
                req = Requirement.objects.create(code=code, catalogue=catalogue, source_version=version, source_record=raw, **fields)
                req.groups.set([groups[g] for g in r['groups']])
                intro, units = clauses(r['requirement'])
                Clause.objects.bulk_create([Clause(requirement=req, ordinal=i, exact_text=u['text'],
                    source_address=f"{fields['source_address']} {u['label'] + '.)' if u['label'] else 'whole requirement'}") for i, u in enumerate(units, 1)])
                continue
            if existing.catalogue_id != catalogue.pk: raise CommandError(f'Requirement code {code} already belongs to another catalogue.')
            changed = [k for k, v in fields.items() if getattr(existing, k) != v]
            if existing.source_record != json.loads(json.dumps(raw, default=str)): changed.append('source_record')
            if set(existing.groups.values_list('code', flat=True)) != set(r['groups']): changed.append('groups')
            units = clauses(r['requirement'])[1]
            if [c.exact_text for c in existing.clauses.order_by('ordinal')] != [u['text'] for u in units]: changed.append('clauses')
            if changed: raise CommandError(f'Stored {code} differs from the source in {", ".join(changed)}; versions are immutable.')
            verified += 1
        stored = Requirement.objects.filter(catalogue=catalogue).count()
        if stored != len(records): raise CommandError(f'Stored {stored} records for this version, source has {len(records)}.')
        for code, group in groups.items():
            resolved = list(Requirement.objects.filter(catalogue=catalogue, groups=group).values_list('question_id', flat=True))
            if len(resolved) != 150 or len(set(resolved)) != 150: raise CommandError(f'{code} resolves to {len(resolved)} records ({len(set(resolved))} distinct).')
        catalogue.report = {**catalogue.report, 'section_name_differences': differences}
        catalogue.save(update_fields=['report'])
        message = (f"{'Imported' if created else 'Verified'} {catalogue.label}: {stored} source records, "
                   f"{len(set(r['question_id'] for r in records))} QuestionIDs, {len(groups)} groups; SHA-256 {source['sha256']}"
                   + (f'; {verified} stored records unchanged' if not created else ''))
        if options['activate'] and catalogue.status != 'active':
            CatalogueVersion.objects.filter(status='active').exclude(pk=catalogue.pk).update(status='retired')
            catalogue.status = 'active'; catalogue.activated_at = timezone.now(); catalogue.activated_by = options['operator']
            catalogue.save(update_fields=['status', 'activated_at', 'activated_by'])
            message += '. Active for new assessments.'
        return message
