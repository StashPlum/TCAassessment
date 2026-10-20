"""V3-03 export check: XLSX/PDF records, JSON archive and report use each demo site's exact group variant (150 rows).

    TCA_V3_SOURCE="V3assessment .xlsx" python manage.py shell < tools/v33_export_check.py
"""
import json
from django.test import Client
from django.contrib.auth import get_user_model
from core.models import Site
from core.assessment_documents import assessment_records
from core.v3_source import read_and_reconcile
import os
_, records, _ = read_and_reconcile(os.environ["TCA_V3_SOURCE"])
c=Client(HTTP_HOST='127.0.0.1'); u=get_user_model().objects.get(username='auditor_demo'); c.force_login(u)
for code,group in (('fictional-stage-one','TCA_v3_GROUP_02'),('fictional-matrix-pilot','TCA_v3_GROUP_12')):
    site=Site.objects.get(code=code)
    draft=site.assessments.filter(status='draft').first()
    exp={r['question_id']:r['requirement'] for r in records if group in r['groups']}
    if draft:
        recs=assessment_records(draft)
        ok=sum(exp[r['Requirement ID']]==r['Official obligation'] for r in recs)
        print(code,'xlsx/pdf records',len(recs),'exact variant',ok)
    a=json.loads(c.get(f'/sites/{code}/assessment/archive/').content)
    print(code,'archive rows',len(a['requirements']),'exact',sum(exp.get(r['id'])==r['official_details'] for r in a['requirements']))
    rep=json.loads(c.get(f'/sites/{code}/report/').content); print(code,'report sections',len(rep['categories']))
