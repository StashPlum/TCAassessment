"""Prepare the hosted demo on every start: catalog, fictional seeds, demo and tester accounts.

Safe to run repeatedly. Passwords come from TCA_DEMO_PASSWORD (never committed). Testers come from
TCA_TESTERS, e.g. "Anna de Boer:auditor, Ben Smit:team, Carla Jansen:manager, Dirk Vos:sensei".
"""
import os, re
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from core.models import CatalogueVersion, Membership, Site, TCAGroup
from core.source import V3_FILES, first_existing

ROLE_MAP={'auditor':'assessor','manager':'manager','sensei':'coach','team':'staff'}
DEMO_SITES=('fictional-stage-one','fictional-matrix-pilot','fictional-harbor')
DEMO_USERS=('demo','auditor_demo','manager_demo','sensei_demo','team_demo','team_demo2','admin_demo')
# Fictional demo configuration only: two sites on groups whose 01.01.C wording differs; Harbor stays unmapped to show the setup blocker.
DEMO_GROUPS={'fictional-stage-one':'TCA_v3_GROUP_02','fictional-matrix-pilot':'TCA_v3_GROUP_12'}

class Command(BaseCommand):
    help='Seed the hosted demo with fictional data and set demo/tester accounts.'

    def handle(self,*args,**options):
        password=os.environ.get('TCA_DEMO_PASSWORD','')
        if len(password)<10: raise CommandError('Set TCA_DEMO_PASSWORD (at least 10 characters) for the hosted demo.')
        call_command('import_demo_catalog')
        for name in ('seed_demo','seed_stage1_demo','seed_stage2_demo','seed_stage4_demo','seed_stage5_demo'):
            call_command(name,verbosity=0)
        User=get_user_model()
        sites=list(Site.objects.filter(code__in=DEMO_SITES))
        admin,_=User.objects.get_or_create(username='admin_demo',defaults={'first_name':'Fictional','last_name':'Administrator'})
        for site in sites: Membership.objects.get_or_create(user=admin,site=site,role='admin')
        self.prepare_v3()
        for user in User.objects.filter(username__in=DEMO_USERS):
            user.set_password(password);user.save(update_fields=['password'])
        created=[]
        for entry in [e.strip() for e in os.environ.get('TCA_TESTERS','').split(',') if e.strip()]:
            if ':' not in entry: raise CommandError(f'Tester "{entry}" needs a role: name:auditor|manager|sensei|team')
            name,role=[part.strip() for part in entry.rsplit(':',1)]
            if role not in ROLE_MAP: raise CommandError(f'Unknown role "{role}" for {name}.')
            username=re.sub(r'[^a-z0-9]+','.',name.lower()).strip('.')[:30] or 'tester'
            first,_,last=name.partition(' ')
            user,new=User.objects.get_or_create(username=username,defaults={'first_name':first[:150],'last_name':last[:150]})
            user.set_password(password);user.save()
            for site in sites: Membership.objects.get_or_create(user=user,site=site,role=ROLE_MAP[role])
            created.append(f'{username} ({role})')
        self.stdout.write('Demo ready. Accounts: '+', '.join(list(DEMO_USERS)+created))

    def prepare_v3(self):
        """Import and activate the private V3 catalogue when its source is provided; otherwise leave the global catalogue."""
        source=first_existing(V3_FILES)
        if source is None:
            self.stdout.write('TCA V3 source not provided; the demo keeps the global catalogue.');return
        call_command('import_v3_catalogue',source=str(source),activate=not CatalogueVersion.objects.filter(status='active').exists(),operator='prepare_demo')
        catalogue=CatalogueVersion.objects.filter(status='active').first()
        if catalogue is None: return
        for code,group in DEMO_GROUPS.items():
            site=Site.objects.filter(code=code,tca_group__isnull=True).first()
            match=TCAGroup.objects.filter(catalogue=catalogue,code=group).first()
            if site and match: site.tca_group=match;site.save(update_fields=['tca_group'])
