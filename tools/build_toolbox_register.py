"""Inspectable field/rule/catalog registers from existing source-backed definitions."""
import sys,csv,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from core.toolbox_registry import REGISTRY
with (root/'docs/kaizen-field-rules.csv').open(encoding='utf-8-sig',newline='') as source:rows=list(csv.DictReader(source))
fields=['Field','Label','Source','Profile','Local rule','Global submission / quality rule','When needed','Storage','Report / export']
with (root/'docs/toolbox-field-rules.csv').open('w',encoding='utf-8',newline='') as target:
    writer=csv.DictWriter(target,fieldnames=fields);writer.writeheader()
    for row in rows:
        local='Required at local closure' if row['Field'] in ('overall_problem','owner','process_location','solution','sustain') else 'Optional draft; relevant extended detail retained'
        writer.writerow(dict(zip(fields,[row['Field'],row['Label'],row['Source'],'small / medium / extensive (detail always retained)',local,row['Classification']+': '+row['When required'],row['When required'],'Kaizen + immutable revisions',row['Report/archive destination']+'; A3 summary where relevant'])))
    for key,label in [('outcome_criterion','Desired outcome / observable criterion'),('observed_result','Actual result and evidence conclusion'),('result_date','Result date')]:
        writer.writerow(dict(zip(fields,[key,label,'Toolbox brief §2; application local gate','all','Required at local closure','No replacement for global before/after observation gates','Local closure','Kaizen.data / revisions','A3 / complete JSON and Excel'])))
    for name,rule in [('attachments','Check-stage result proof required locally; optional draft; stage/requirement links'),('worksheets','Optional selected methods; validated causes require evidence and explanation'),('input_profile','Required at new creation; legacy retained for existing events'),('local_status','Derived only through local checks; separate from global review')]:
        writer.writerow(dict(zip(fields,[name,name,'Toolbox brief §§1–5','all',rule,'Global review unchanged; missing User Guide remains explicit','Relevant workflow step','Separate models / event revisions','Full JSON/ZIP; method CSV/SVG; A3 selected summary'])))
catalog=[]
for spec in REGISTRY.values():catalog.append({k:v for k,v in spec.items() if k!='defaults'})
(root/'docs/toolbox-catalog.json').write_text(json.dumps({'verified_on':'2026-10-14','methods':catalog,'calculation_reference':'https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc322.htm'},indent=2,ensure_ascii=False),encoding='utf-8')
print(f'Generated {len(rows)+7} field/rule rows and {len(catalog)} method specifications.')
