"""Catalog for the hosted demo.

Uses the private extracted catalog when it is provided as a secret file (never committed) and its recorded
source hash matches the known workbook; otherwise creates a clearly labelled synthetic 15 x 10 catalog.
An existing catalog is never changed.
"""
import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Category, Clause, Requirement, SourceVersion
from core.source import CATALOG_FILES, first_existing

KNOWN_SHA256='3c0a8616b3d81d574f7460942a3e16bab61565e593ef8d25a53cca89d4d8c77a'
NAME='TCA assessment work categorisation.xlsx'

class Command(BaseCommand):
    help='Load the private catalog extract if present, otherwise a synthetic demo catalog.'

    @transaction.atomic
    def handle(self,*args,**options):
        if Requirement.objects.exists():
            self.stdout.write(f'Catalog already present ({Requirement.objects.count()} requirements); unchanged.');return
        path=first_existing(CATALOG_FILES)
        if path:
            data=json.loads(path.read_text(encoding='utf-8'))
            if data.get('sha256')!=KNOWN_SHA256: raise CommandError('The catalog extract does not match the known source workbook hash.')
            if len(data['categories'])!=15 or len(data['requirements'])!=150: raise CommandError('Catalog extract has an unexpected structure.')
            source=SourceVersion.objects.create(filename=NAME,sha256=data['sha256'])
            for c in data['categories']: Category.objects.create(number=c['number'],name=c['name'],source_address=c['source'])
            for r in data['requirements']:
                req=Requirement.objects.create(code=r['id'],category_id=r['category_number'],level_code=r['level_code'],position=r['position'],
                    detail_text=r['detail_text'],reasoning=r['reasoning'] or '',expected_evidence=r['expected_evidence'] or '',
                    remote_method=r['remote_method'] or '',source_address=r['source'],source_version=source)
                Clause.objects.bulk_create([Clause(requirement=req,ordinal=i,source_address=c['address'],exact_text=c['text']) for i,c in enumerate(r['clauses'],1)])
            self.stdout.write(f'Imported the private catalog extract: 15 sections, 150 requirements, {Clause.objects.count()} clauses.')
            return
        source=SourceVersion.objects.create(filename='Synthetic demo catalog (official wording not loaded)',sha256='0'*64)
        for number in range(1,16):
            category=Category.objects.create(number=number,name=f'Synthetic section {number}',source_address='Synthetic')
            for position in range(1,11):
                level='C' if position<=5 else 'B' if position<=8 else 'A'
                req=Requirement.objects.create(code=f'{number}.{level}.{position}',category=category,position=position,level_code=level,
                    detail_text='SYNTHETIC demo requirement: official TCA wording is not loaded in this demo.',
                    expected_evidence='Synthetic expected evidence',remote_method='Synthetic remote method',source_address='Synthetic',source_version=source)
                Clause.objects.create(requirement=req,ordinal=1,source_address='Synthetic',exact_text='Synthetic clause text for the demo.')
        self.stdout.write('Created the synthetic demo catalog (15 x 10). Add the private catalog file to show official wording.')
