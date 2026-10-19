"""Synthetic, idempotent stage 5 demonstration: a finalised fictional Kaizen shared as learning and
validated as best practice for the fictional matrix site. Only fictional seed records are touched."""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from core.a3 import ensure_reports
from core.kaizen import checkpoint
from core.models import BestPracticeValidation, Evidence, EventAttachment, Kaizen, LearningEntry, Membership, Site
from core.report_views import learning_approach

class Command(BaseCommand):
    help='Share one fictional finalised Kaizen as validated learning with Fictional Matrix Pilot.'

    def handle(self,*args,**options):
        call_command('seed_stage4_demo',verbosity=0);call_command('seed_stage2_demo',verbosity=0)
        source=Site.objects.get(code='fictional-stage-one');target=Site.objects.get(code='fictional-matrix-pilot')
        event=Kaizen.objects.get(site=source,title='FICTIONAL pre-shift meeting with a fixed agenda')
        if LearningEntry.objects.filter(event=event).exists():
            self.stdout.write('Stage 5 fictional learning already exists; nothing changed.');return
        User=get_user_model();sensei=User.objects.get(username='sensei_demo');manager=User.objects.get(username='manager_demo')
        with transaction.atomic():
            event=Kaizen.objects.select_for_update().get(pk=event.pk)
            if event.status=='results_under_review':
                checkpoint(event,sensei,'Before fictional finalisation')
                event.data={**event.data,'coach_review':'FICTIONAL: results hold for eight weeks; agenda card is in standard work.'}
                event.status='verified';event.revision+=1;event.save();checkpoint(event,sensei,'Fictional stage 5 finalisation')
            reports=ensure_reports(event,sensei)
            entry=LearningEntry.objects.create(event=event,report=reports[0],title=event.title,context='FICTIONAL: hall 2, three shifts, team leaders rotate.',
                transfer_limits='FICTIONAL: check your own shift pattern and board location before adopting.',approach=learning_approach(event),
                approved_by=manager,approval_reason='FICTIONAL pilot sharing for the stage 5 demonstration')
            entry.allowed_sites.set([source,target])
            BestPracticeValidation.objects.create(entry=entry,validated_by=User.objects.get(username='auditor_demo'),how_achieved='FICTIONAL: fixed slot and agenda card, sustained by a weekly manager check.',
                validation_basis='FICTIONAL: eight weeks of board data at the source site.')
            evidence=Evidence.objects.create(site=source,title='FICTIONAL PDCA board photo week 41',evidence_type='observation',owner='Mila Janssen',created_by=sensei)
            EventAttachment.objects.create(event=event,stage='Check',evidence=evidence,title='Board photo',version='1',provenance='Existing fictional evidence',created_by=sensei)
        self.stdout.write('Stage 5 fictional learning shared with Fictional Matrix Pilot and validated as best practice.')
