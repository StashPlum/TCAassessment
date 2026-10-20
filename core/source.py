"""Source text helpers; all returned wording comes from extracted original cells."""
import json
from functools import lru_cache
from pathlib import Path

import os
ROOT=Path(__file__).resolve().parents[1]
# The hosted demo receives extracted sources as private secret files; they are never committed.
SECRET_DIR=Path(os.environ.get('TCA_SOURCE_DIR','/etc/secrets'))
KAIZEN_FILES=(ROOT/'sources/extracted/Global_Kaizen_Template_20241219.json',SECRET_DIR/'kaizen-template.json')
CATALOG_FILES=(ROOT/'sources/extracted/TCA assessment work categorisation.json',SECRET_DIR/'tca-catalog.json')
# TCA V3 workbook (private): the original .xlsx or its JSON row extract, from TCA_V3_SOURCE or a secret file.
V3_FILES=tuple(Path(p) for p in [os.environ.get('TCA_V3_SOURCE',''),SECRET_DIR/'tca-v3-source.json',SECRET_DIR/'V3assessment .xlsx',ROOT/'sources/original/V3assessment .xlsx'] if str(p))

def first_existing(paths):
    return next((path for path in paths if path.is_file()),None)

def synthetic_kaizen_record():
    """Clearly labelled stand-in when the private template extract is absent (hosted demo without secret file)."""
    coach=[{'address':f'C{78+i}','value':f'Synthetic quality criterion {i} (template text not loaded)'} for i in range(1,11)]
    coach+=[{'address':f'B{row}','value':f'Supplemental template field B{row}'} for row in range(1,111)]
    drops=[{'address':f'Z{4+i}','value':value} for i,value in enumerate(['Work Instruction','Performance Board','Checklist','Training Record'])]
    return {'sheets':[{'name':'COACH REVIEW','cells':coach},{'name':'DROP_DOWNS','cells':drops}],'defined_names':{},'synthetic':True}

@lru_cache(maxsize=1)
def kaizen_record():
    path=first_existing(KAIZEN_FILES)
    return json.loads(path.read_text(encoding='utf-8')) if path else synthetic_kaizen_record()

def star_criteria():
    sheet=next(s for s in kaizen_record()['sheets'] if s['name']=='COACH REVIEW')
    cells={c['address']:c['value'] for c in sheet['cells']}
    return [(i,cells[f'C{i+78}'],f'COACH REVIEW!C{i+78}') for i in range(1,11)]

def document_types():
    sheet=next(s for s in kaizen_record()['sheets'] if s['name']=='DROP_DOWNS')
    cells={c['address']:c['value'] for c in sheet['cells']}
    return [(cells[f'Z{i}'],cells[f'Z{i}']) for i in range(4,18) if cells.get(f'Z{i}')]

def coach_labels(rows):
    sheet=next(s for s in kaizen_record()['sheets'] if s['name']=='COACH REVIEW')
    cells={c['address']:c['value'] for c in sheet['cells']}
    return [(i,cells[f'B{i}']) for i in rows]

def source_taxonomies():
    """Inspectable source list suggestions; unresolved/broken names are not evaluated."""
    import re
    record=kaizen_record();names=record['defined_names']
    rows={c['address']:c['value'] for c in next(s for s in record['sheets'] if s['name']=='DROP_DOWNS')['cells']}
    result={}
    for name,definition in names.items():
        match=re.match(r'OFFSET\(DROP_DOWNS!\$([A-Z]+)\$(\d+),0,0,COUNTA',str(definition))
        if not match or '#REF!' in definition: continue
        column,start=match.groups();items=[]
        for address,value in rows.items():
            cell=re.fullmatch(r'([A-Z]+)(\d+)',address)
            if cell and cell[1]==column and int(cell[2])>=int(start) and isinstance(value,str) and value.strip() and value not in items:items.append(value)
        result[name]={'definition':definition,'values':items,'source':'DROP_DOWNS!'+column+start}
    return result
