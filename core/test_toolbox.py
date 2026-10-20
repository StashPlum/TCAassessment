from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.management import call_command
from .models import *
import json
from uuid import uuid4
from copy import deepcopy
from .toolbox_registry import REGISTRY,initial_payload,migrate_payload
from .toolbox_math import calculate,validate_payload

def data_rows(rows,meta=None):
    return {'meta':meta or {},'rows':[{'id':str(uuid4()),'archived':False,**r} for r in rows],'conclusion':'Synthetic conclusion','links':{'actions':[],'observations':[],'evidence':[]},'include_in_a3':True}

class ProfileTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('profile-test',password='test-password')
        self.site=Site.objects.create(name='Synthetic profile site',code='profile-site')
        Membership.objects.create(user=self.user,site=self.site,role='staff')
        self.event=Kaizen.objects.create(site=self.site,title='Synthetic test',profile='BP',created_by=self.user,data={'overall_problem':'Original text','extra_85':'Keep every detail'})
        self.client.force_login(self.user)

    def test_up_down_switch_preserves_and_stale_rejected(self):
        url=reverse('input_profile',args=[self.site.code,self.event.pk])
        for revision,size in enumerate(('extensive','small','medium')):
            self.assertEqual(self.client.post(url,{'revision':revision,'input_profile':size}).status_code,302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.data['extra_85'],'Keep every detail')
        self.assertEqual(self.event.profile,'BP')
        self.assertEqual(self.event.input_profile,'medium')
        self.assertEqual(self.client.post(url,{'revision':0,'input_profile':'small'}).status_code,409)
        self.assertEqual(self.event.history.count(),4)
        self.assertContains(self.client.get(reverse('kaizen_detail',args=[self.site.code,self.event.pk])),'Desired outcome')

    def test_local_route_does_not_bypass_global(self):
        url=reverse('kaizen_detail',args=[self.site.code,self.event.pk])
        response=self.client.post(url,{'revision':0,'action':'close_local'})
        self.assertContains(response,'Check-stage result evidence')
        self.event.refresh_from_db();self.assertEqual(self.event.local_status,'open')
        self.assertEqual(self.event.status,'proposed')
        self.assertContains(self.client.post(url,{'revision':0,'action':'submit_review'}),'Before submitting')

    def test_suggestions_and_profile_creation(self):
        from .profiles import suggest_profile
        self.assertEqual(suggest_profile(True,True,True)[0],'extensive')
        self.assertEqual(suggest_profile(False,True,False)[0],'medium')
        response=self.client.post(reverse('kaizens',args=[self.site.code]),{'title':'New fictional draft','input_profile':'small','profile':'A3'})
        self.assertEqual(response.status_code,302)
        created=Kaizen.objects.latest('pk')
        self.assertEqual((created.input_profile,created.profile),('small','A3'))

class ToolboxTests(ProfileTests):
    def test_worksheet_csrf_site_isolation_and_review_permission(self):
        from django.test import Client
        other=Site.objects.create(name='Synthetic isolated site',code='isolated-tool')
        outsider=get_user_model().objects.create_user('isolated-user',password='test-password');Membership.objects.create(user=outsider,site=other,role='staff')
        w=Worksheet.objects.create(event=self.event,method='pareto',title='Synthetic private tool',stage='Check',payload=initial_payload('pareto'))
        url=reverse('worksheet',args=[self.site.code,self.event.pk,w.pk]);client=Client(enforce_csrf_checks=True);client.force_login(self.user)
        self.assertEqual(client.post(url,json.dumps({'revision':0,'event_revision':0,'payload':w.payload}),content_type='application/json').status_code,403)
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.get(reverse('worksheet_export',args=[other.code,self.event.pk,w.pk,'json'])).status_code,404)
    def test_every_catalog_worksheet_roundtrip_and_exports(self):
        self.assertGreaterEqual(len(REGISTRY),39)
        for key,spec in REGISTRY.items():
            with self.subTest(method=key):
                self.assertGreaterEqual(len(spec['fields']),3)
                self.event.refresh_from_db()
                response=self.client.post(reverse('toolbox',args=[self.site.code,self.event.pk]),{'method':key,'stage':spec['stage'],'revision':self.event.revision})
                self.assertEqual(response.status_code,302)
                w=Worksheet.objects.latest('pk');payload=deepcopy(w.payload)
                # A representative structured draft, with numeric/select values where relevant.
                row={'id':str(uuid4()),'archived':False}
                for f in spec['fields']:
                    row[f['key']]=f['choices'][0] if f['type']=='select' else '2' if f['type']=='number' else 'Synthetic '+f['key']
                for special in ('parent','next','evidence_id','before_attachment','after_attachment','worksheet_id'): row.pop(special,None)
                payload['rows'].append(row);self.event.refresh_from_db()
                url=reverse('worksheet',args=[self.site.code,self.event.pk,w.pk])
                result=self.client.post(url,json.dumps({'revision':0,'event_revision':self.event.revision,'payload':payload}),content_type='application/json')
                self.assertEqual(result.status_code,200,result.content)
                w.refresh_from_db();self.assertEqual(w.payload['rows'][-1],row)
                self.assertContains(self.client.get(url),spec['name'])
                for fmt in ('json','csv','svg'):
                    response=self.client.get(reverse('worksheet_export',args=[self.site.code,self.event.pk,w.pk,fmt]))
                    self.assertEqual(response.status_code,200)
                    if fmt=='json': self.assertEqual(response.json()['payload'],w.payload)
                    if fmt=='svg':
                        import xml.etree.ElementTree as ET
                        ET.fromstring(response.content)

    def test_dynamic_causes_branches_restore_and_conflicts(self):
        event=self.event
        payload=data_rows([{'category':'Method','cause':'Long hypothesis '*50,'state':'hypothesis'} for _ in range(17)],{'effect':'Synthetic effect','categories':'Method\nPeople'})
        payload['rows'][1]['parent']=payload['rows'][0]['id']
        w=Worksheet.objects.create(event=event,method='ishikawa',stage='Plan',title='Ishikawa',payload=payload)
        from .toolbox_views import worksheet_checkpoint
        worksheet_checkpoint(w,self.user)
        changed=deepcopy(payload);changed['rows'][0]['category']='People';changed['rows'][2]['archived']=True
        url=reverse('worksheet',args=[self.site.code,event.pk,w.pk])
        response=self.client.post(url,json.dumps({'revision':0,'event_revision':0,'payload':changed}),content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(self.client.post(url,json.dumps({'revision':0,'event_revision':0,'payload':changed}),content_type='application/json').status_code,409)
        response=self.client.post(url,json.dumps({'revision':1,'event_revision':1,'restore':0}),content_type='application/json')
        self.assertEqual(response.status_code,200);w.refresh_from_db();self.assertEqual(w.payload,payload)
        branches=data_rows([{'branch':'Main' if i<6 else 'Other','question':'Why?','answer':'Unverified hypothesis'} for i in range(12)])
        branches['rows'][7]['parent']=branches['rows'][6]['id'];validate_payload('5whys',branches)
        with self.assertRaises(ValueError): migrate_payload('ishikawa',payload,1,2)
        branches['rows'][6]['parent']=branches['rows'][7]['id']
        with self.assertRaises(ValueError):validate_payload('5whys',branches)

    def test_independent_calculation_fixtures(self):
        result=calculate('pareto',data_rows([{'category':'A','value':10,'unit':'count'},{'category':'B','value':30,'unit':'count'},{'category':'A','value':10,'unit':'count'}],{'unit':'count'}))
        self.assertEqual([(s['label'],s['value'],s['cumulative']) for s in result['series']],[('B',30,60),('A',20,100)])
        zero=calculate('pareto',data_rows([{'category':'A','value':0,'unit':'count'}]));self.assertIsNone(zero['series'][0]['cumulative'])
        with self.assertRaises(ValueError): validate_payload('pareto',data_rows([{'value':-1}]))
        mixed=calculate('pareto',data_rows([{'category':'A','value':1,'unit':'count'},{'category':'B','value':2,'unit':'EUR'}]));self.assertTrue(mixed['incomplete'])
        histogram=calculate('histogram',data_rows([{'value':i,'unit':'s'} for i in (0,1,2,3,4)],{'bins':2}));self.assertEqual([s['value'] for s in histogram['series']],[2,3])
        control=calculate('control-chart',data_rows([{'value':i,'unit':'s','period':str(i)} for i in range(1,21)]))
        self.assertAlmostEqual(control['center'],10.5);self.assertAlmostEqual(control['ucl'],13.16);self.assertAlmostEqual(control['mr_ucl'],3.267)
        scatter=calculate('scatter',data_rows([{'x':i,'y':i*2,'x_unit':'count','y_unit':'s'} for i in range(4)]));self.assertAlmostEqual(scatter['correlation'],1)
        box=calculate('boxplot',data_rows([{'group':'A','value':i,'unit':'s'} for i in [1,2,3,4,100]]));self.assertEqual(box['series'][0]['median'],3);self.assertEqual(box['series'][0]['outliers'],[100])
        takt=calculate('takt',data_rows([{'process':'Pick','cycle':3,'unit':'min'}],{'available':480,'demand':240,'unit':'min','period':'shift'}));self.assertEqual(takt['takt'],2)
        oee=calculate('oee',data_rows([{'asset':'Line','planned':100,'run':90,'ideal_cycle':.95,'total':90,'good':89.1,'unit':'min','period':'shift','source':'fixture'}]));self.assertAlmostEqual(oee['series'][0]['value'],84.645)
        path=calculate('spaghetti',data_rows([{'route':'R','state':'current','x':0,'y':0,'unit':'m'},{'route':'R','state':'current','x':3,'y':4,'unit':'m'}]));self.assertEqual(path['routes'][0]['distance'],5)
        matrix=calculate('decision-matrix',data_rows([{'option':'A','criterion':'Quality','weight':2,'score':4},{'option':'A','criterion':'Effort','weight':1,'score':1}]));self.assertEqual(matrix['series'][0]['value'],3)
        self.assertTrue(calculate('oee',data_rows([{'asset':'L','planned':0}]))['incomplete'])
