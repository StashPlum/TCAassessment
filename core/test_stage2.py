"""Visual-milestone domain checks: matrix, filters, links and honest scope."""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from .matrix import assessment_matrix
from .models import Assessment, Kaizen, Membership, Opportunity, Requirement, Response, Site


class StageTwoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_catalog',verbosity=0)
        cls.site=Site.objects.create(name='Synthetic Matrix',code='stage-two')
        cls.other=Site.objects.create(name='Private Matrix',code='other-stage-two')
        cls.auditor=get_user_model().objects.create_user('visual-auditor')
        Membership.objects.create(user=cls.auditor,site=cls.site,role='assessor')
        cls.assessment=Assessment.objects.create(site=cls.site,version=1,created_by=cls.auditor,policy_version='advisory-v2')
        cls.y=Requirement.objects.get(code='1.C.1')
        cls.a=Requirement.objects.get(code='1.C.2')
        cls.n=Requirement.objects.get(code='2.C.1')
        for req,code in [(cls.y,'Y'),(cls.a,'A'),(cls.n,'N')]:
            Response.objects.create(assessment=cls.assessment,requirement=req,code=code,
                conclusion='Synthetic detail for '+code,
                advisory_follow_up='Synthetic retest next time' if code=='A' else '',updated_by=cls.auditor)
        cls.finding=Opportunity.objects.create(site=cls.site,requirement=cls.a,kind='verification',problem='Synthetic follow-up action')
        cls.event=Kaizen.objects.create(site=cls.site,title='Synthetic linked Kaizen',profile='A4',created_by=cls.auditor)
        cls.event.linked_requirements.add(cls.a)

    def test_standard_matrix_150_cells_and_answer_detail_match(self):
        matrix=assessment_matrix(self.assessment)
        self.assertEqual((matrix['sections_count'],matrix['requirements_count'],len(matrix['positions'])),(15,150,10))
        self.assertEqual([(g['title'],g['count']) for g in matrix['groups']],
                         [('Certified',5),('Advanced',3),('Showcase',2)])
        self.assertEqual([cell['state'] for cell in matrix['rows'][0]['cells'][:3]],['yes','advisory','unanswered'])
        self.client.force_login(self.auditor)
        page=self.client.get(reverse('opportunities',args=[self.site.code]))
        self.assertEqual(page.status_code,200)
        self.assertContains(page,f'1.C.2 · {escape(self.a.category.name)} · A · Advisory')
        self.assertNotContains(page,'Authorized locations')
        detail=self.client.get(reverse('respond',args=[self.site.code,self.a.code]))
        for expected in ('A · Advisory','Synthetic detail for A','Synthetic retest next time',
                         'Synthetic follow-up action','Synthetic linked Kaizen'):
            self.assertContains(detail,expected)
        self.assertEqual(self.client.get(reverse('opportunities',args=[self.other.code])).status_code,404)

    def test_matrix_filters_and_empty_results(self):
        self.client.force_login(self.auditor)
        url=reverse('opportunities',args=[self.site.code])
        advisory=self.client.get(url,{'state':'advisory'})
        self.assertEqual([row['category'].number for row in advisory.context['matrix']['rows']],[1])
        self.assertContains(advisory,'1 active')
        no_result=self.client.get(url,{'q':'NO_SUCH_REQUIREMENT_987'})
        self.assertEqual(no_result.context['matrix']['rows'],[])
        self.assertContains(no_result,'No sections match')
        conduct=self.client.get(reverse('assessment',args=[self.site.code]),{'answer':'A'})
        self.assertEqual(conduct.context['page'].paginator.count,1)
        self.assertEqual(conduct.context['page'].object_list[0].code,self.a.code)
        self.assertContains(conduct,'Filters active')

    def test_alternate_frozen_scope_does_not_invent_150_cells(self):
        alt=Assessment.objects.create(site=self.site,version=2,created_by=self.auditor,
            scope_snapshot={'version':'synthetic approved alternative','requirements':['1.C.1','2.C.2'],
                            'known':True,'basis':'Synthetic approved alternate scope fixture'})
        matrix=assessment_matrix(alt)
        self.assertTrue(matrix['known'])
        self.assertEqual((matrix['sections_count'],matrix['requirements_count'],matrix['positions']),(2,2,[1,2]))
        self.assertEqual(matrix['rows'][0]['cells'][1]['state'],'outside')
        self.assertEqual(matrix['rows'][1]['cells'][0]['state'],'outside')
        self.client.force_login(self.auditor)
        page=self.client.get(reverse('opportunities',args=[self.site.code]))
        self.assertContains(page,'2 sections · 2 requirements')
        self.assertNotContains(page,'15 sections · 150 requirements')

    def test_overview_keeps_assessed_pass_advisory_and_cat_separate(self):
        self.client.force_login(self.auditor)
        page=self.client.get(reverse('home'))
        self.assertContains(page,'Assessed')
        self.assertContains(page,'Meets local rule')
        self.assertContains(page,'Open Advisory')
        self.assertContains(page,'CAT confirmation pending')
        self.assertNotContains(page,'Authorized locations')
        self.assertEqual(self.client.get(reverse('locations')).status_code,200)
