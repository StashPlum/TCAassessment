"""Direct-URL authorisation probe against the local baseline demo (GET only)."""
import json, requests, re
BASE='http://127.0.0.1:8000'; PW=__import__('os').environ['TCA_DEMO_PASSWORD']
S='fictional-stage-one'; F='fictional-harbor'
routes={
 'site progress':'/sites/{s}/','assessment':'/sites/{s}/assessment/','configuration':'/sites/{s}/assessment/configuration/',
 'new draft (GET)':'/sites/{s}/assessment/new/','approve (GET)':'/sites/{s}/assessment/approve/','history':'/sites/{s}/assessment/history/',
 'history xlsx':'/sites/{s}/assessment/history/export/xlsx/','sessions':'/sites/{s}/sessions/','matrix':'/sites/{s}/opportunities/',
 'kaizen list':'/sites/{s}/kaizen/','review queue':'/sites/{s}/kaizen/review/','review export xlsx':'/sites/{s}/kaizen/review/export/xlsx/',
 'kaizen 1':'/sites/{s}/kaizen/1/','kaizen 1 review':'/sites/{s}/kaizen/1/review/','kaizen 1 archive':'/sites/{s}/kaizen/1/archive/',
 'kaizen 1 excel':'/sites/{s}/kaizen/1/excel/','kaizen 1 export pdf':'/sites/{s}/kaizen/1/export/pdf/','a3 report 1':'/sites/{s}/kaizen/1/a3/1/',
 'attachment 1':'/sites/{s}/kaizen/1/attachments/1/download/','evidence':'/sites/{s}/evidence/','preparation':'/sites/{s}/evidence/preparation/',
 'prep export xlsx':'/sites/{s}/evidence/preparation/export/xlsx/','evidence 1 download':'/sites/{s}/evidence/1/download/',
 'claims':'/sites/{s}/verification/','learning':'/sites/{s}/learning/','resources':'/sites/{s}/resources/','report':'/sites/{s}/report/',
 'administration':'/administration/','locations':'/locations/','feedback list':'/feedback/list/','django admin':'/admin/',
}
users=['auditor_demo','manager_demo','sensei_demo','team_demo','team_demo2','demo']
out={}
for u in users:
    s=requests.Session(); s.get(BASE+'/login/'); tok=s.cookies['csrftoken']
    s.post(BASE+'/login/',data={'username':u,'password':PW,'csrfmiddlewaretoken':tok},headers={'Referer':BASE+'/login/'})
    out[u]={}
    for name,r in routes.items():
        for site in ((S,F) if '{s}' in r else (S,)):
            url=r.format(s=site); resp=s.get(BASE+url,allow_redirects=False)
            key=name+(' [own]' if site==S else ' [other site]') if '{s}' in r else name
            out[u][key]=resp.status_code if resp.status_code!=302 else '302→'+resp.headers.get('Location','')[:20]
json.dump(out,open(__import__('os').environ.get('V3_OUT','output')+'/rbac_probe.json','w'),indent=1)
keys=list(out['auditor_demo'])
print(f"{'route':38}"+''.join(f'{u[:9]:>11}' for u in users))
for k in keys: print(f'{k[:38]:38}'+''.join(f'{str(out[u][k])[:10]:>11}' for u in users))
