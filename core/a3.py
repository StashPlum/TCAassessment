"""Saved-data A3 summary + full structured archive; no source-template parity claim."""
from io import BytesIO
from html import escape
import hashlib
from django.core.files.base import ContentFile
from django.db import transaction
from reportlab.lib.pagesizes import A3,landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether,Image
from svglib.svglib import svg2rlg
from .models import A3Report
from .kaizen import snapshot,public_snapshot
from .measurements import compare_observations
from .toolbox_visuals import render_svg
from .toolbox_registry import REGISTRY
from .toolbox_math import calculate
RENDERER_VERSION=2

def report_snapshot(event):
    # A3 is a broadly readable summary: no participant/benefit/restricted file data.
    content=public_snapshot(snapshot(event),False,False)
    content['site']=event.site.name;content['event_id']=event.pk;content['event_revision']=event.revision
    content['comparisons']=compare_observations(event.observations.all())
    return content

def summary_sections(content):
    data=content['data']
    return [('Plan · problem and intended outcome', '\n'.join(str(data.get(k,'')) for k in ['overall_problem','process_location','outcome_criterion','specific_problem','root_cause'])),
            ('Do · change and actions',str(data.get('solution',''))+'\n'+'\n'.join(f'{a["description"]} · owner {a["owner"]} · {a.get("end_date") or "date unset"}' for a in content['actions'] if a['phase']=='DO')),
            ('Check · actual result',str(data.get('observed_result',''))+'\n'+str(data.get('result_date',''))+'\n'+'\n'.join(f'{c["measure"]} · {c["population"]}: before {c["before_average"]} ({c["before_count"]}), after {c["after_average"]} ({c["after_count"]}), change {c["difference"]} {c["unit"]}' for c in content.get('comparisons',[]))),
            ('Act · sustain and follow-up','\n'.join(str(data.get(k,'')) for k in ['sustain','sustain_owner','sustain_check','next_kaizen_action'])+'\n'+'\n'.join(f'{a["description"]} · {a["owner"]}' for a in content['actions'] if a['phase']=='ACT'))]

def build_pdf(content,photo_bytes=None):
    output=BytesIO();width,height=landscape(A3);styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='A3Title',fontName='Helvetica-Bold',fontSize=22,leading=27,textColor=colors.HexColor('#051039'),spaceAfter=10))
    styles.add(ParagraphStyle(name='A3Body',fontSize=11,leading=15,spaceAfter=7))
    styles.add(ParagraphStyle(name='A3Small',fontSize=9,leading=12,textColor=colors.HexColor('#475569')))
    doc=SimpleDocTemplate(output,pagesize=(width,height),rightMargin=32,leftMargin=32,topMargin=32,bottomMargin=40,title=f'TCA Progress A3 · {content["title"]}')
    def para(value,style='A3Body'): return Paragraph(escape(str(value)).replace('\n','<br/>'),styles[style])
    story=[para(content['title'],'A3Title'),para(f'{content["site"]} · event {content["event_id"]} · revision {content["event_revision"]} · input {content["input_profile"]} · methodological type {content["profile"]} · local {content["local_status"]} / global {content["status"]}','A3Small'),Spacer(1,15)]
    cells=[]
    for heading,value in summary_sections(content):
        # Concise summary is explicitly shortened; the saved archive is never mutated.
        concise=value if len(value)<=750 else value[:750]+'\n[Summary shortened; complete wording in the event archive.]'
        cells.append([para(heading,'Heading2'),para(concise or 'Not recorded')])
    table=Table([[cells[0],cells[1]],[cells[2],cells[3]]],colWidths=[(width-80)/2]*2,hAlign='LEFT')
    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.8,colors.HexColor('#bccada')),('INNERGRID',(0,0),(-1,-1),.5,colors.HexColor('#bccada')),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story.extend([table,Spacer(1,10),para('A3 report format does not change event type or TCA classification. Local summary; CAT confirmation and official submission policy remain separate. Full data, original files and revision history remain in the private event archive.','A3Small')])
    worksheets=[w for w in content.get('worksheets',[]) if w.get('include_in_a3') and w['method'] in REGISTRY]
    for w in worksheets:
        story.extend([PageBreak(),para(w['title'],'A3Title'),para(f'{w["stage"]} · schema v{w["schema_version"]} · worksheet r{w["revision"]}','A3Small')])
        analysis=calculate(w['method'],w['payload'])
        for message in analysis['messages']: story.append(para(message))
        story.append(para(analysis['formula'],'A3Small'))
        drawing=svg2rlg(BytesIO(render_svg(w['method'],w['payload']).encode('utf-8')))
        if drawing:
            factor=min((width-90)/drawing.width,(height-270)/drawing.height,1)
            # Very large diagrams are kept readable through a summary + complete SVG.
            if factor<.45:
                story.append(para('Full diagram exceeds a readable A3 scale. See complete SVG / worksheet in archive; the first active items are summarized below.'))
                fields=REGISTRY[w['method']]['fields']
                for row in [r for r in w['payload']['rows'] if not r.get('archived')][:12]:
                    story.append(para(' · '.join(f'{f["label"]}: {row.get(f["key"],"")}' for f in fields)[:500]))
            else:
                drawing.scale(factor,factor);drawing.width*=factor;drawing.height*=factor;story.append(drawing)
        conclusion=w['payload'].get('conclusion','')
        story.append(Spacer(1,10));story.append(para('Conclusion / next test','Heading2'));story.append(para(conclusion[:1800]+(' [Summary shortened; full archive retained.]' if len(conclusion)>1800 else '') or 'Not recorded'))
        story.append(para('Method source: '+REGISTRY[w['method']]['source'],'A3Small'))
        if w['method']=='5s' and photo_bytes:
            for row in w['payload'].get('rows',[]):
                if row.get('archived'):continue
                for key,label in [('before_attachment','Before'),('after_attachment','After')]:
                    identifier=str(row.get(key,''))
                    if identifier in photo_bytes:
                        image=Image(BytesIO(photo_bytes[identifier]));factor=min(450/image.imageWidth,240/image.imageHeight,1);image.drawWidth=image.imageWidth*factor;image.drawHeight=image.imageHeight*factor
                        story.append(KeepTogether([para(f'{row.get("pillar","")} · {label} photo (attachment #{identifier})','Heading3'),image]))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',9);canvas.setFillColor(colors.HexColor('#475569'));canvas.drawString(32,22,f'TCA Progress · synthetic/local pilot · event {content["event_id"]} r{content["event_revision"]} · complete archive retained');canvas.drawRightString(width-32,22,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()

def ensure_report(event,user):
    """Event is locked by caller; reports are immutable at each finalization revision."""
    existing=event.a3_reports.filter(event_revision=event.revision,renderer_version=RENDERER_VERSION).first()
    if existing:return existing
    content=report_snapshot(event)
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    content=json.loads(json.dumps(content,cls=DjangoJSONEncoder))
    photos={}
    from pathlib import Path
    for item in event.attachments.filter(classification='internal'):
        file=item.file;name=item.original_name
        if item.evidence and item.evidence.site_id==event.site_id and item.evidence.classification=='internal':file=item.evidence.file;name=file.name if file else ''
        if file and Path(name).suffix.lower() in ('.png','.jpg','.jpeg'):
            with file.open('rb') as stream:photos[str(item.pk)]=stream.read()
    raw=build_pdf(content,photos);version=(event.a3_reports.order_by('-version').values_list('version',flat=True).first() or 0)+1
    report=A3Report(event=event,event_revision=event.revision,renderer_version=RENDERER_VERSION,version=version,snapshot=content,sha256=hashlib.sha256(raw).hexdigest(),created_by=user)
    report.file.save(f'kaizen-{event.pk}-a3-v{version}.pdf',ContentFile(raw),save=False);report.save();return report
