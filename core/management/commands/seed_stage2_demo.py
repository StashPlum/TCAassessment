"""Idempotent, fully populated fictional matrix for the stage-two visual review."""
from datetime import date
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.models import Assessment, Coverage, Evidence, Kaizen, Membership, Opportunity, Requirement, Response, Site
from core.readiness import assessment_snapshot


class Command(BaseCommand):
    help='Create a separate fictional 56 Y / 19 Advisory / 75 N assessment matrix.'

    @transaction.atomic
    def handle(self,*args,**options):
        site,created=Site.objects.get_or_create(code='fictional-matrix-pilot',defaults={
            'name':'Fictional Matrix Pilot','country_code':'NL','grouping':'Benelux','target_level':'C'})
        users={}
        for username,role in [('auditor_demo','assessor'),('manager_demo','manager'),
                              ('sensei_demo','coach'),('team_demo','staff'),('demo','assessor')]:
            user=get_user_model().objects.filter(username=username).first()
            if user:
                Membership.objects.get_or_create(user=user,site=site,role=role)
                users[role]=user
        if not created:
            self.stdout.write('Fictional matrix site already exists; assessment and work records unchanged.')
            return
        auditor=get_user_model().objects.get(username='auditor_demo')
        manager=users.get('manager')
        team=users.get('staff')
        if not manager or not team: raise ValueError('Run seed_stage1_demo before seed_stage2_demo.')
        requirements=list(Requirement.objects.prefetch_related('clauses').order_by('category_id','position'))
        if len(requirements)!=150: raise ValueError('The original 150-requirement catalog must be imported first.')
        evidence=Evidence.objects.create(site=site,title='FICTIONAL matrix evidence for accepted clauses',
            evidence_type='document',owner='Fictional auditor',source='Synthetic visual fixture only',created_by=auditor)
        assessment=Assessment.objects.create(site=site,version=1,policy_version='advisory-v2',created_by=auditor,
            rationale='FICTIONAL fully populated matrix for responsive review')
        now=timezone.now();answers=[];coverage=[];by_code={}
        for index,req in enumerate(requirements):
            bucket=(index*37)%150
            code='Y' if bucket<56 else 'A' if bucket<75 else 'N'
            by_code[req.code]=code
            answers.append(Response(assessment=assessment,requirement=req,code=code,
                conclusion='FICTIONAL accepted current clause evidence' if code in ('Y','A') else 'FICTIONAL gap remains',
                advisory_follow_up='FICTIONAL retest the open control next assessment' if code=='A' else '',
                advisory_retest_status='due_next' if code=='A' else 'not_due',updated_by=auditor))
            if code in ('Y','A'):
                for clause in req.clauses.all():
                    coverage.append(Coverage(evidence=evidence,clause=clause,accepted=True,
                        decision='FICTIONAL clause-level review',reviewed_by=auditor,reviewed_at=now))
        Coverage.objects.bulk_create(coverage)
        Response.objects.bulk_create(answers)
        assessment.status='approved';assessment.approved_by=manager;assessment.approved_at=now
        assessment.snapshot=assessment_snapshot(site,assessment);assessment.save()
        n_req=next(req for req in requirements if by_code[req.code]=='N')
        a_req=next(req for req in requirements if by_code[req.code]=='A')
        Opportunity.objects.create(site=site,requirement=n_req,kind='operational',
            problem='FICTIONAL close the operational control gap',owner='team_demo',due_date=date(2026,11,20))
        finding=Opportunity.objects.create(site=site,requirement=a_req,kind='verification',
            problem='FICTIONAL retest the Advisory follow-up',owner='team_demo',due_date=date(2026,12,1))
        event=Kaizen.objects.create(site=site,opportunity=finding,title='FICTIONAL Advisory action',
            profile='A4',input_profile='small',created_by=team,
            data={'overall_problem':finding.problem,'owner':'team_demo'})
        event.linked_requirements.add(a_req)
        self.stdout.write('Created isolated fictional matrix: 56 Y, 19 Advisory, 75 N; 150 assessed, 75 accepted passes.')
