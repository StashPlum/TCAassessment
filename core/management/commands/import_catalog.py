import hashlib
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Category, Clause, Requirement, SourceVersion

ROOT = Path(__file__).resolve().parents[3]
NAME = 'TCA assessment work categorisation.xlsx'

class Command(BaseCommand):
    help = 'Import exact original TCA wording transactionally and without duplicate records.'
    @transaction.atomic
    def handle(self, *args, **kwargs):
        original = ROOT / 'sources' / 'original' / NAME
        extracted = ROOT / 'sources' / 'extracted' / 'TCA assessment work categorisation.json'
        data = json.loads(extracted.read_text(encoding='utf-8'))
        actual = hashlib.sha256(original.read_bytes()).hexdigest()
        if actual != data['sha256']:
            raise CommandError('Original source hash differs from extracted source; re-extract and review.')
        if len(data['categories']) != 15 or len(data['requirements']) != 150:
            raise CommandError('Catalog count differs from expected source structure.')
        source, _ = SourceVersion.objects.get_or_create(filename=NAME, defaults={'sha256': actual})
        if source.sha256 != actual:
            raise CommandError('Previously imported source has changed; use a reviewed new version.')
        for c in data['categories']:
            obj, created = Category.objects.get_or_create(number=c['number'], defaults={'name': c['name'], 'source_address': c['source']})
            if not created and (obj.name != c['name'] or obj.source_address != c['source']):
                raise CommandError(f'Existing category {obj.number} differs from source')
        for r in data['requirements']:
            fields = {'category_id': r['category_number'], 'level_code': r['level_code'], 'position': r['position'],
                      'detail_text': r['detail_text'], 'reasoning': r['reasoning'] or '',
                      'expected_evidence': r['expected_evidence'] or '', 'remote_method': r['remote_method'] or '',
                      'source_address': r['source'], 'source_version': source}
            obj, created = Requirement.objects.get_or_create(code=r['id'], defaults=fields)
            if not created and any(getattr(obj, k) != v for k, v in fields.items()):
                raise CommandError(f'Existing requirement {obj.code} differs from immutable source')
            for i, clause in enumerate(r['clauses'], 1):
                item, made = Clause.objects.get_or_create(requirement=obj, ordinal=i,
                    defaults={'source_address': clause['address'], 'exact_text': clause['text']})
                if not made and (item.source_address != clause['address'] or item.exact_text != clause['text']):
                    raise CommandError(f'Existing clause {obj.code}/{i} differs from source')
            if obj.clauses.count() != len(r['clauses']):
                raise CommandError(f'Clause count differs for {obj.code}')
        self.stdout.write(self.style.SUCCESS(f'Imported/verified {Category.objects.count()} categories, {Requirement.objects.count()} requirements, {Clause.objects.count()} clauses; SHA-256 {actual}'))
