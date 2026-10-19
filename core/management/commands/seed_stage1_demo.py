"""Synthetic, idempotent role and Advisory demonstration; no original records edited."""
from datetime import date
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.assessment_config import frozen_configuration
from core.models import Assessment,Coverage,Evidence,Kaizen,KaizenAction,Membership,Opportunity,Requirement,Response,Site,SiteQuestionVersion
from core.readiness import assessment_snapshot


class Command(BaseCommand):
    help='Create isolated fictional role dashboards and a versioned Advisory assessment.'

    @transaction.atomic
    def handle(self,*args,**options):
        site,created=Site.objects.get_or_create(code='fictional-stage-one',defaults={
            'name':'Fictional Advisory Pilot','country_code':'NL','grouping':'Benelux','target_level':'C'})
        users={}
        for role,name in [('assessor','auditor_demo'),('manager','manager_demo'),('coach','sensei_demo'),('staff','team_demo')]:
            user,new=get_user_model().objects.get_or_create(username=name,defaults={'is_staff':False})
            if new:
                user.set_password('LocalDemo2026!');user.save(update_fields=['password'])
            Membership.objects.get_or_create(user=user,site=site,role=role)
            users[role]=user
        demo=get_user_model().objects.filter(username='demo').first()
        if demo: Membership.objects.get_or_create(user=demo,site=site,role='assessor')
        if not created:
            self.stdout.write('Fictional stage-one site already exists; no assessment or events changed.')
            return
        reqs=list(Requirement.objects.filter(category_id=1,position__lte=5))
        first=reqs[0]
        SiteQuestionVersion.objects.create(site=site,requirement=first,version=1,kind='local_guidance',
            question_text='How does the fictional site demonstrate this safety control?',
            evidence_items=['Synthetic local check record','Current work instruction'],
            local_explanation='Fictional interviewer wording; global clauses still control the decision.',
            change_reason='Demonstrate site wording without altering official obligations',author=users['assessor'],
            diff={'question_text':{'before':first.detail_text,'after':'How does the fictional site demonstrate this safety control?'}})
        evidence=Evidence.objects.create(site=site,title='FICTIONAL reviewed source for five controls',
            evidence_type='document',owner='Fictional auditor',source='Synthetic only',created_by=users['assessor'])
        for req in reqs:
            for clause in req.clauses.all():
                Coverage.objects.create(evidence=evidence,clause=clause,accepted=True,decision='FICTIONAL clause review',
                    reviewed_by=users['assessor'],reviewed_at=timezone.now())
        assessment=Assessment.objects.create(site=site,version=1,policy_version='advisory-v2',status='draft',
            created_by=users['assessor'],configuration_snapshot=frozen_configuration(site),
            rationale='FICTIONAL stage-one Advisory example')
        for index,req in enumerate(reqs):
            advisory=index==2
            Response.objects.create(assessment=assessment,requirement=req,code='A' if advisory else 'Y',
                conclusion='FICTIONAL evidence reviewed; improvement remains' if advisory else 'FICTIONAL accepted clause evidence',
                advisory_follow_up='FICTIONAL verify the updated work instruction at the next assessment' if advisory else '',
                advisory_retest_status='due_next' if advisory else 'not_due',updated_by=users['assessor'])
        assessment.status='approved';assessment.approved_by=users['manager'];assessment.approved_at=timezone.now()
        assessment.snapshot=assessment_snapshot(site,assessment);assessment.save()
        finding=Opportunity.objects.create(site=site,requirement=reqs[2],kind='operational',
            problem='FICTIONAL improve repeat safety checks',owner='team_demo',due_date=date(2026,11,30))
        event=Kaizen.objects.create(site=site,opportunity=finding,title='FICTIONAL safety check improvement',
            profile='A4',input_profile='small',created_by=users['staff'],data={'overall_problem':finding.problem,'owner':'team_demo'})
        event.linked_requirements.add(reqs[2])
        KaizenAction.objects.create(event=event,phase='DO',description='FICTIONAL test the revised work instruction',
            owner='team_demo',start_date=date(2026,10,20),end_date=date(2026,11,1))
        self.stdout.write('Created FICTIONAL Advisory site. auditor_demo, manager_demo, sensei_demo and team_demo use the local demo password.')
