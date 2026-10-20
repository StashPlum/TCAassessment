"""Write the two private files for the hosted demo into the ignored output/render-secrets/ folder.

tca-catalog.json      = the extracted assessment catalog (official wording), unchanged.
kaizen-template.json  = only the Kaizen template parts the app reads (COACH REVIEW, DROP_DOWNS, defined names).
Upload them in Render as Secret Files. They must never be committed.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'sources/extracted'
OUT=ROOT/'output/render-secrets'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    catalog=(SOURCE/'TCA assessment work categorisation.json').read_bytes()
    (OUT/'tca-catalog.json').write_bytes(catalog)
    kaizen=json.loads((SOURCE/'Global_Kaizen_Template_20241219.json').read_text(encoding='utf-8'))
    slim={'sha256':kaizen.get('sha256'),'defined_names':kaizen.get('defined_names',{}),
          'sheets':[{'name':s['name'],'cells':s['cells']} for s in kaizen['sheets'] if s['name'] in ('COACH REVIEW','DROP_DOWNS')]}
    (OUT/'kaizen-template.json').write_text(json.dumps(slim,ensure_ascii=False),encoding='utf-8')
    for path in sorted(OUT.iterdir()): print(f'{path.name}: {path.stat().st_size//1024} KB -> {path}')

if __name__=='__main__': main()
