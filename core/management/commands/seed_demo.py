from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Assessment, Coverage, Evidence, Membership, Requirement, Response, Site
from core.readiness import assessment_snapshot

class Command(BaseCommand):
    help = 'Create a clearly fictional local demonstration site and account.'
    def handle(self,*args,**kwargs):
        site,_=Site.objects.get_or_create(code='fictional-harbor',defaults={'name':'Fictional Harbor Site','target_level':'B'})
        user,created=get_user_model().objects.get_or_create(username='demo',defaults={'is_staff':False})
        if created:
            user.set_password('LocalDemo2026!');user.save()
        for role in ('staff','assessor','coach','manager'):
            Membership.objects.get_or_create(user=user,site=site,role=role)
        examples,new=Site.objects.get_or_create(code='fictional-maturity',defaults={'name':'Fictional Maturity Examples','target_level':'A'})
        # Explicit synthetic location metadata; never infer country for other sites.
        for fixture,country,grouping in ((site,'NL','Benelux'),(examples,'GB','UK')):
            if not fixture.country_code:
                fixture.country_code=country;fixture.grouping=grouping
                fixture.save(update_fields=['country_code','grouping'])
        for role in ('staff','assessor','coach','manager'):
            Membership.objects.get_or_create(user=user,site=examples,role=role)
        if new:
            assessment=Assessment.objects.create(site=examples,version=1,status='approved',created_by=user,
                approved_by=user,approved_at=timezone.now(),rationale='Fictional examples for the unapproved local draft policy')
            for category,limit in ((1,5),(2,8),(3,10)):
                for req in Requirement.objects.filter(category_id=category,position__lte=limit):
                    evidence=Evidence.objects.create(site=examples,title=f'FICTIONAL coverage for {req.code}',
                        evidence_type='observation',owner='Fictional assessor',source='Synthetic demonstration only',created_by=user)
                    for clause in req.clauses.all():
                        Coverage.objects.create(evidence=evidence,clause=clause,accepted=True,decision='Synthetic accepted clause example',reviewed_by=user,reviewed_at=timezone.now())
                    Response.objects.create(assessment=assessment,requirement=req,code='Y',conclusion='Synthetic accepted requirement for local scoring demonstration',updated_by=user)
            assessment.snapshot=assessment_snapshot(examples,assessment)
            assessment.save(update_fields=['snapshot'])
        self.stdout.write(self.style.SUCCESS('Fictional demo: demo / LocalDemo2026! at /login/'))
