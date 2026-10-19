"""Additive, idempotent synthetic toolbox fixtures; no existing records are edited."""
from datetime import date,timedelta
from decimal import Decimal
from uuid import uuid4
from pathlib import Path
from io import BytesIO
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from openpyxl import Workbook
from core.models import *
from core.readiness import assessment_snapshot
from core.kaizen import checkpoint
from core.toolbox_views import worksheet_checkpoint
from core.toolbox_registry import initial_payload

class Command(BaseCommand):
    help='Add fictional 45/150 coverage and toolbox journey fixtures; existing fixture rows are not rewritten.'
    @transaction.atomic
    def handle(self,*args,**options):
        user=get_user_model().objects.get(username='demo')
        site,created=Site.objects.get_or_create(code='fictional-toolbox',defaults={'name':'Fictional Toolbox Pilot','country_code':'NL','grouping':'Benelux'})
        recipient,_=Site.objects.get_or_create(code='fictional-learning',defaults={'name':'Fictional Learning Recipient','country_code':'BE','grouping':'Benelux'})
        for place in (site,recipient):
            for role in ('staff','assessor','coach','manager'):Membership.objects.get_or_create(user=user,site=place,role=role)
        if not created:
            self.stdout.write('Synthetic toolbox fixtures already exist; no records changed.');return
        requirements=list(Requirement.objects.all())
        evidence=Evidence.objects.create(site=site,title='FICTIONAL clause verification source',owner='Synthetic assessor',version='1',source='Fictional fixture; no production evidence',evidence_type='document',created_by=user)
        Coverage.objects.bulk_create([Coverage(evidence=evidence,clause=c,accepted=True,decision='FICTIONAL reviewed detail',reviewed_by=user,reviewed_at=timezone.now()) for c in Clause.objects.filter(requirement__in=requirements[:51])])
        assessment=Assessment.objects.create(site=site,version=1,policy_version='draft-v1',created_by=user,rationale='FICTIONAL 45/150 baseline')
        Response.objects.bulk_create([Response(assessment=assessment,requirement=r,code='Y' if i<45 else 'N',conclusion='FICTIONAL reviewed baseline',updated_by=user) for i,r in enumerate(requirements)])
        assessment.status='approved';assessment.approved_at=timezone.now();assessment.approved_by=user;assessment.snapshot=assessment_snapshot(site,assessment);assessment.save()
        for size,title,kind in [('medium','FICTIONAL reduce label rework','A3'),('extensive','FICTIONAL full packaging investigation','BP')]:
            event=Kaizen.objects.create(site=site,title=title,profile=kind,input_profile=size,created_by=user,status='results_under_review' if size=='medium' else 'proposed',
                data={'overall_problem':'FICTIONAL labels cause repeat picking checks','specific_problem':'FICTIONAL two labels conflict at packing','owner':'demo','process_location':site.name,
                      'outcome_criterion':'Observe fewer repeat checks with intact traceability','root_cause':'Hypothesis: label placement is inconsistent; test on observed handling.',
                      'solution':'FICTIONAL standardize label position and test','baseline':'10','actual':'8','target':'8','measure':'Repeat checks','unit':'count','population':'Synthetic shifts','direction':'down',
                      'data_source':'FICTIONAL recorded shifts','observed_result':'FICTIONAL repeat checks fell from 10 to 8 in comparable shifts','result_date':'2026-10-14',
                      'sustain':'FICTIONAL daily standard check','sustain_owner':'demo','sustain_check':'Check adoption on 2026-10-21','coach_review':'','star_7':'N','star_8':'N'})
            KaizenAction.objects.create(event=event,phase='DO',description='FICTIONAL move and test labels',owner='demo',start_date=date(2026,9,1),end_date=date(2026,9,2))
            KaizenAction.objects.create(event=event,phase='ACT',description='FICTIONAL check the standard each shift',owner='demo')
            if size=='medium':
                for phase,days,value in [('before',[0,1],10),('after',[2,9,16,23,30,37],8)]:
                    for day in days:
                        at=date(2026,9,1)+timedelta(days=day)
                        Observation.objects.create(event=event,phase=phase,measure='Repeat checks',value=value,unit='count',population='Synthetic shifts',period_start=at,period_end=at,data_source='FICTIONAL recorded shifts')
                p=initial_payload('pareto',event);p['meta']={'metric':'frequency','unit':'count','aggregation':'sum'}
                p['rows']=[{'id':str(uuid4()),'category':name,'value':value,'unit':'count','source':'FICTIONAL check sheet','archived':False} for name,value in [('Label',30),('Placement',15),('Damage',5)]]
                p['conclusion']='Label observations dominate these fictional counts; validate the placement hypothesis.'
                w=Worksheet.objects.create(event=event,method='pareto',title='FICTIONAL Pareto of repeat checks',stage='Check',payload=p);worksheet_checkpoint(w,user)
                p=initial_payload('ishikawa',event)
                p['rows']=[{'id':str(uuid4()),'category':name,'cause':cause,'state':'hypothesis','test':'Observe and compare locally','archived':False} for name,cause in [('Method','Label position differs'),('People','Work standard is unclear'),('Material','Labels overlap'),('Equipment / machines','Print alignment varies'),('Measurement','Definitions differ'),('Environment','Lighting needs checking')]]
                p['rows'].append({'id':str(uuid4()),'category':'Method','parent':p['rows'][0]['id'],'cause':'Alternative placement sequence','state':'hypothesis','test':'Test the handling sequence','archived':False})
                w=Worksheet.objects.create(event=event,method='ishikawa',title='FICTIONAL cause investigation',stage='Plan',payload=p);worksheet_checkpoint(w,user)
                event.linked_requirements.add(*requirements[45:51])
                for r in requirements[45:51]:
                    claim=VerificationClaim.objects.create(site=site,event=event,requirement=r,statement='FICTIONAL ready with reviewed clause evidence',created_by=user);claim.evidence.add(evidence)
            else:
                Participant.objects.create(event=event,first_initial='F',last_name='Fictional',kaizen_role='Synthetic team leader',role_profile='Synthetic',estimated_hours=2)
                event.data.update({f'coach_{r}':'FICTIONAL '+str(r)+' — guide-dependent source field retained' for r in [11,14,19,20,21,22,23,24,28,29,30,31,33,35,38,40,41,43,47,48,49,50,51,52,54,57,60,61,62,64,66,75]})
                event.data.update({f'fivew2h_{key}':'FICTIONAL '+key for key in ['why','where','who','what','when','how','how_many']});event.save()
            checkpoint(event,user,'Synthetic toolbox demonstration fixture')
        folder=Path('fixtures/toolbox');folder.mkdir(parents=True,exist_ok=True)
        (folder/'synthetic-check.csv').write_text('phase,measure,value,unit,population,date,source\nbefore,Repeat checks,10,count,Synthetic shifts,2026-10-01,Fictional CSV\nafter,Repeat checks,8,count,Synthetic shifts,2026-10-14,Fictional CSV\n',encoding='utf-8')
        workbook=Workbook();sheet=workbook.active;sheet.title='Fictional observations';sheet.append(['phase','measure','value','unit','population','date','source']);sheet.append(['before','Repeat checks',10,'count','Synthetic shifts','2026-10-01','Fictional Excel']);sheet.append(['after','Repeat checks',8,'count','Synthetic shifts','2026-10-14','Fictional Excel']);workbook.save(folder/'synthetic-observations.xlsx')
        self.stdout.write('Created fictional 45/150 baseline, six pending unique claims, medium/extensive events and a separate learning recipient. Existing rows untouched.')
