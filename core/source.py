"""Source text helpers; all returned wording comes from extracted original cells."""
import json
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def kaizen_record():
    path=ROOT/'sources/extracted/Global_Kaizen_Template_20241219.json'
    return json.loads(path.read_text(encoding='utf-8'))

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
