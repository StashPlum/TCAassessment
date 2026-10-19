"""Copy and render actual synthetic reports for human visual inspection."""
import os,sys,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
from core.models import A3Report
from pypdf import PdfReader
import pdfplumber
folder=root/'output/pdf';folder.mkdir(parents=True,exist_ok=True)
rendered=root/'tmp/pdfs';rendered.mkdir(parents=True,exist_ok=True)
results=[]
for name,title in [('small','FICTIONAL quick packing check'),('medium','FICTIONAL reduce label rework'),('extensive','FICTIONAL full packaging investigation')]:
    report=A3Report.objects.filter(event__title=title).order_by('-version').first()
    if not report:raise SystemExit('Report not finalized: '+title)
    with report.file.open('rb') as stream:raw=stream.read()
    path=folder/f'toolbox-{name}-a3.pdf';path.write_bytes(raw)
    reader=PdfReader(path);outside=[]
    with pdfplumber.open(path) as pdf:
        for i,page in enumerate(pdf.pages,1):
            outside += [(i,c['text']) for c in page.chars if c['x0']<0 or c['x1']>page.width+1 or c['top']<0 or c['bottom']>page.height+1]
    assert not outside,(name,outside)
    subprocess.run(['pdftoppm','-r','85','-png',str(path),str(rendered/f'toolbox-{name}')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    results.append({'profile':name,'report_id':report.pk,'version':report.version,'event_revision':report.event_revision,'pages':len(reader.pages),'page_size':[float(reader.pages[0].mediabox.width),float(reader.pages[0].mediabox.height)],'out_of_page_characters':len(outside)})
print(json.dumps(results,indent=2))
