"""CI uses explicitly synthetic source labels/catalog, never internal workbooks.

The full local suite additionally verifies original wording/494 clauses. This
runner verifies new domain behavior without distributing those source files.
"""
import os,sys
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
from django.core.management import call_command
from core.models import SourceVersion,Category,Requirement,Clause

def synthetic_catalog(self,*args,**kwargs):
    source,_=SourceVersion.objects.get_or_create(filename='Synthetic CI catalog',defaults={'sha256':'0'*64})
    for category in range(1,16):
        cat,_=Category.objects.get_or_create(number=category,defaults={'name':f'Synthetic section {category}','source_address':'Synthetic'})
        for position in range(1,11):
            level='C' if position<=5 else 'B' if position<=8 else 'A';code=f'{category}.{level}.{position}'
            req,_=Requirement.objects.get_or_create(code=code,defaults={'category':cat,'position':position,'level_code':level,'detail_text':'Synthetic requirement fixture','source_address':'Synthetic','source_version':source})
            Clause.objects.get_or_create(requirement=req,ordinal=1,defaults={'source_address':'Synthetic','exact_text':'Synthetic detail fixture'})

with patch('core.forms.star_criteria',return_value=[(i,f'Synthetic quality criterion {i}',f'Synthetic!C{i}') for i in range(1,11)]), \
     patch('core.forms.document_types',return_value=[('Work Instruction','Work Instruction'),('Performance Board','Performance Board')]), \
     patch('core.management.commands.import_catalog.Command.handle',synthetic_catalog):
    call_command('test','core.test_toolbox','core.test_progress_files','core.test_reports',verbosity=1)
