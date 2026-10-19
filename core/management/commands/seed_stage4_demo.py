"""Synthetic, idempotent stage 4 demonstration: team, tasks, Gantt, sensei review and reports.

Adds fictional Kaizen events to the fictional stage-one site only; existing records are never edited.
"""
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.kaizen import checkpoint
from core.models import Kaizen, KaizenAction, Membership, Observation, Participant, Requirement, ReviewNote, Site

TITLES=('FICTIONAL pre-shift meeting with a fixed agenda','FICTIONAL dock waiting time','FICTIONAL label errors at packing')

class Command(BaseCommand):
    help='Create fictional stage 4 Kaizen events with team, tasks, observations and review states.'

    def handle(self,*args,**options):
        call_command('seed_stage1_demo',verbosity=0)
        site=Site.objects.get(code='fictional-stage-one')
        if Kaizen.objects.filter(site=site,title__in=TITLES).exists():
            self.stdout.write('Stage 4 fictional events already exist; nothing changed.');return
        with transaction.atomic(): self.create(site)
        self.stdout.write('Stage 4 fictional events created on Fictional Advisory Pilot.')

    def create(self,site):
        User=get_user_model();users={u.username:u for u in User.objects.filter(username__in=['team_demo','sensei_demo','manager_demo','auditor_demo'])}
        helper,new=User.objects.get_or_create(username='team_demo2',defaults={'first_name':'Daan','last_name':'Visser'})
        if new: helper.set_password('LocalDemo2026!');helper.save(update_fields=['password'])
        Membership.objects.get_or_create(user=helper,site=site,role='staff')
        for name,(first,last) in {'team_demo':('Mila','Janssen'),'sensei_demo':('Ingrid','Holm'),'manager_demo':('Sander','de Vries'),'auditor_demo':('Pieter','Claes')}.items():
            user=users[name]
            if not user.first_name: user.first_name,user.last_name=first,last;user.save(update_fields=['first_name','last_name'])
        today=timezone.localdate();d=lambda days: today+timedelta(days=days)
        requirement=Requirement.objects.filter(code='4.C.3').first()

        def member(event,user,role):
            return Participant.objects.create(event=event,user=user,first_initial=user.first_name[:1] or user.username[:1],last_name=user.last_name or user.username,kaizen_role=role)

        def observations(event,before,after,points):
            for phase,value,offset in [('before',before,-60),('after',after,-20)]:
                for i in range(points):
                    Observation.objects.create(event=event,phase=phase,measure='Shifts with a pre-shift meeting',value=value,unit='%',population='Hall 2 shifts',
                        period_start=d(offset+i),period_end=d(offset+i),data_source='FICTIONAL attendance board')

        # 1. Submitted for review: complete PDCA, team and tasks.
        lead=users['team_demo']
        event=Kaizen.objects.create(site=site,title=TITLES[0],profile='A4',input_profile='medium',created_by=lead,status='results_under_review',submitted_at=timezone.now(),
            data={'overall_problem':TITLES[0],'owner':'Mila Janssen','process_location':'Hall 2','specific_problem':'FICTIONAL: when it is busy the pre-shift meeting is skipped; 40% of shifts had none in June.',
                  'root_cause':'FICTIONAL: no fixed time or agenda; the meeting depended on the team leader.','solution':'FICTIONAL: fixed 10-minute slot at the board with a five-point agenda card.',
                  'measure':'Shifts with a pre-shift meeting','baseline':'60','target':'95','actual':'96','unit':'%','population':'Hall 2 shifts','data_source':'FICTIONAL attendance board',
                  'sustain':'FICTIONAL: attendance on the board; weekly check by the site manager.','observed_result':'FICTIONAL: 96% of shifts held the meeting.'})
        if requirement: event.linked_requirements.add(requirement)
        m_lead=member(event,lead,'Kaizen lead');m_help=member(event,helper,'Team member');member(event,users['sensei_demo'],'Sensei')
        for phase,text,who,start,end,progress in [('PLN','Measure current meeting attendance',m_lead,-40,-33,100),('DO','Print and place the agenda card',m_help,-30,-26,100),
                ('DO','Train team leaders on the fixed slot',m_lead,-25,-12,100),('CHK','Compare four weeks of attendance',m_help,-10,3,60),('ACT','Add the agenda card to standard work',m_lead,2,12,0)]:
            KaizenAction.objects.create(event=event,phase=phase,description='FICTIONAL '+text.lower(),owner=f'{who.user.first_name} {who.user.last_name}',assignee=who,start_date=d(start),end_date=d(end),progress=progress)
        observations(event,60,96,8)
        event.revision=1;event.save();checkpoint(event,lead,'Fictional stage 4 seed')

        # 2. Returned with sensei feedback per phase.
        returned=Kaizen.objects.create(site=site,title=TITLES[1],profile='A3',input_profile='extensive',created_by=helper,status='in_progress',submitted_at=timezone.now()-timedelta(days=3),
            data={'overall_problem':TITLES[1],'owner':'Daan Visser','specific_problem':'FICTIONAL: trucks wait 38 minutes on average at docks 3 to 6.','solution':'FICTIONAL: staging lanes per dock.'})
        member(returned,helper,'Kaizen lead');member(returned,lead,'Team member')
        KaizenAction.objects.create(event=returned,phase='DO',description='FICTIONAL mark staging lanes',owner='Mila Janssen',assignee=returned.participants.get(user=lead),start_date=d(-5),end_date=d(9),progress=40)
        for stage,text in [('Plan','FICTIONAL: an A3 event needs the cause analysis; add the spaghetti diagram findings.'),('Check','FICTIONAL: record at least five after points before submitting again.')]:
            ReviewNote.objects.create(event=returned,stage=stage,kind='return',text=text,actor=users['sensei_demo'],event_revision=0)
        returned.revision=1;returned.save();checkpoint(returned,helper,'Fictional stage 4 seed')

        # 3. Draft with a task for the team member.
        draft=Kaizen.objects.create(site=site,title=TITLES[2],profile='A4',input_profile='small',created_by=lead,
            data={'overall_problem':TITLES[2],'owner':'Mila Janssen'})
        m=member(draft,lead,'Kaizen lead')
        KaizenAction.objects.create(event=draft,phase='PLN',description='FICTIONAL collect a week of label error counts',owner='Mila Janssen',assignee=m,start_date=d(0),end_date=d(6),progress=20)
        checkpoint(draft,lead,'Fictional stage 4 seed')
