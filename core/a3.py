"""Saved-data A3/A4 report + full structured archive; no source-template parity claim.

Paper size is a report choice only. The first page follows the Global Kaizen template report tabs
(A3 landscape = LANDSCAPE tab, A4 portrait = PORTRAIT tab, see a3_sheet.py); every shortened value
continues in full in the "Complete content" pages, so no saved source content is dropped to fit.
"""
from io import BytesIO
from html import escape
from pathlib import Path
import hashlib
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A3,A4,landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.graphics.shapes import Drawing,Rect,String
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether,Image
from svglib.svglib import svg2rlg
from .models import A3Report
from .kaizen import snapshot,public_snapshot,gate_list,review_state,REVIEW_STATE_LABELS,team_display
from .measurements import compare_observations
from .methodology import rules_for
from .toolbox_visuals import render_svg
from .toolbox_registry import REGISTRY
from .toolbox_math import calculate
RENDERER_VERSION=4
PAPERS={'A3':landscape(A3),'A4':A4}
NAVY=colors.HexColor('#0B1A48');MUTED=colors.HexColor('#4B5265');LINE=colors.HexColor('#D8DBE3');RED=colors.HexColor('#E4002B')
LOGO=Path(__file__).resolve().parent/'static/core/ceva-logo.png'
PHASE_LABELS={'PLN':'Plan','DO':'Do','CHK':'Check','ACT':'Act'}

def report_snapshot(event):
    # Broadly readable summary: no participant contact/hours, benefits or restricted files.
    content=public_snapshot(snapshot(event),False,False)
    content['site']=event.site.name;content['event_id']=event.pk;content['event_revision']=event.revision
    content['comparisons']=compare_observations(event.observations.all())
    content['gates']=gate_list(event)
    content['review_state']=REVIEW_STATE_LABELS[review_state(event)]
    content['method_rules']=rules_for(event.profile)['summary']
    # Team names and Kaizen roles only; contact details and hours stay in the restricted archive.
    content['team']=[{'name':team_display(p),'role':p.kaizen_role} for p in event.participants.select_related('user')]
    names={p.pk:team_display(p) for p in event.participants.select_related('user')}
    for action in content['actions']: action['assignee_name']=names.get(action.get('assignee_id'),'')
    from .a3_sheet import header_fields
    content['header']=header_fields(event,content['team'])
    content['feedback']=[{'stage':n.stage,'kind':n.kind,'text':n.text,'resolved':n.resolved} for n in event.review_notes.exclude(kind='reply')]
    return content

def _lines(data,keys):
    return '\n'.join(str(data.get(k,'')).strip() for k in keys if str(data.get(k,'')).strip())

def _action_line(a):
    period=f'{a.get("start_date") or "start unset"} – {a.get("end_date") or "end unset"}'
    owner=a.get('assignee_name') or a.get('owner','')
    return f'{PHASE_LABELS.get(a["phase"],a["phase"])} · {a["description"]} · {owner} · {period} · {a.get("progress",0)}%'

def _n(value):
    if value in (None,''): return 'missing'
    try: return f'{float(value):g}'
    except (TypeError,ValueError): return str(value)

def report_blocks(content):
    """The six numbered A3 blocks in full; the sheet shortens them, continuation pages do not."""
    data=content['data'];actions=content.get('actions',[])
    results=[f'{c["measure"]} · {c["population"]} · {c["unit"]}: before {_n(c["before_average"])} ({c["before_count"]} points), after {_n(c["after_average"])} ({c["after_count"]} points), change {_n(c["difference"])}' for c in content.get('comparisons',[])]
    context='\n'.join([f'{label}: {value}' for label,value in content.get('header',[]) if str(value).strip()]+
        [f'{label}: {data[key]}' for label,key in [('Why important','fivew2h_why'),('Problem area','coach_49'),('Problem process','coach_50'),('Who','fivew2h_who'),
         ('When','fivew2h_when'),('Product / service','fivew2h_what'),('Solution area','coach_60'),('Solution process','coach_61'),("Site manager's comments",'coach_35')] if str(data.get(key,'')).strip()])
    return [('0','Context',context),('1','Problem',_lines(data,['overall_problem','process_location','outcome_criterion','specific_problem'])),
            ('2','Cause',_lines(data,['root_cause','cause_status'])),
            ('3','Countermeasure',_lines(data,['solution'])),
            ('4','Actions','\n'.join(_action_line(a) for a in actions)),
            ('5','Result','\n'.join([_lines(data,['observed_result','result_date'])]+results).strip()),
            ('6','Sustainment','\n'.join([_lines(data,['sustain','sustain_owner','sustain_check','next_kaizen_action'])]+
                [f'{d["document_type"]} · {d["name"]} · {d["updated_at"]}' for d in content.get('document_updates',[])]).strip())]

def summary_sections(content):
    """Preview sections for the web page, PDCA-ordered and complete."""
    return [(f'{number} · {title}',value) for number,title,value in report_blocks(content)]

def _result_drawing(comparison,width):
    before=comparison.get('before_average');after=comparison.get('after_average')
    if before is None or after is None: return None
    top=max(abs(float(before)),abs(float(after)),1);bar=width-150
    drawing=Drawing(width,46)
    for y,label,value,fill in [(26,'Before',float(before),colors.HexColor('#9AA1B2')),(4,'After',float(after),colors.HexColor('#2F7D45'))]:
        drawing.add(String(0,y+4,label,fontName='Helvetica',fontSize=8,fillColor=MUTED))
        drawing.add(Rect(42,y,bar,14,fillColor=colors.HexColor('#F3F4F7'),strokeColor=None))
        drawing.add(Rect(42,y,bar*abs(value)/top,14,fillColor=fill,strokeColor=None))
        drawing.add(String(48+bar,y+4,f'{value:g} {comparison["unit"]}',fontName='Helvetica-Bold',fontSize=8,fillColor=NAVY))
    return drawing

def _styles(paper):
    small=paper=='A4';styles=getSampleStyleSheet();base=8.5 if small else 10.5
    styles.add(ParagraphStyle(name='A3Title',fontName='Helvetica-Bold',fontSize=16 if small else 22,leading=20 if small else 27,textColor=NAVY,spaceAfter=4))
    styles.add(ParagraphStyle(name='A3Body',fontSize=base,leading=base*1.35,spaceAfter=4))
    styles.add(ParagraphStyle(name='A3Small',fontSize=base-1.5,leading=(base-1.5)*1.35,textColor=MUTED))
    styles.add(ParagraphStyle(name='A3Block',fontName='Helvetica-Bold',fontSize=base+2,leading=(base+2)*1.3,textColor=NAVY,spaceAfter=3))
    styles.add(ParagraphStyle(name='A3Banner',fontName='Helvetica-Bold',fontSize=base,leading=base*1.35,textColor=colors.HexColor('#8E1D17')))
    cell=6.6 if small else 9
    styles.add(ParagraphStyle(name='Cell',fontSize=cell,leading=cell*1.25))
    styles.add(ParagraphStyle(name='Small',fontSize=cell-.6,leading=(cell-.6)*1.25,textColor=MUTED))
    styles.add(ParagraphStyle(name='Label',fontName='Helvetica-Bold',fontSize=cell-.6,leading=(cell-.6)*1.25,textColor=NAVY))
    styles.add(ParagraphStyle(name='SheetTitle',fontName='Helvetica-Bold',fontSize=14 if small else 18,leading=17 if small else 22,textColor=NAVY))
    styles.add(ParagraphStyle(name='Banner',fontName='Helvetica-Bold',fontSize=cell+.4,leading=(cell+.4)*1.3,textColor=colors.HexColor('#8E1D17')))
    styles.add(ParagraphStyle(name='Band',fontName='Helvetica-Bold',fontSize=cell+2,leading=(cell+2)*1.3,textColor=colors.white,backColor=NAVY,borderPadding=(2,4,2,4),spaceAfter=4))
    return styles

def _event_story(content,photo_bytes,paper,final,styles):
    width,height=PAPERS[paper];small=paper=='A4';margin=24 if small else 32
    def para(value,style='A3Body'): return Paragraph(escape(str(value)).replace('\n','<br/>'),styles[style])
    from .a3_sheet import template_sheet
    story,_=template_sheet(content,paper,final,styles,width,margin)
    blocks=report_blocks(content);gates=content.get('gates',[])
    story.append(para('Report paper does not change event type or TCA classification. Local summary; official submission policy remains separate.','A3Small'))
    # Complete content: every block, action, gate, team role and review item in full.
    story.extend([PageBreak(),para('Complete content','A3Title'),para('Full wording of every block. Nothing on the summary sheet is omitted here.','A3Small')])
    for number,title,value in blocks: story.extend([para(f'{number}  {title}','A3Block'),para(value or 'Not recorded'),Spacer(1,4)])
    rows=[['Phase','Action','Owner','Start','End','Progress']]+[[PHASE_LABELS.get(a['phase'],a['phase']),para(a['description'],'A3Small'),a.get('assignee_name') or a.get('owner',''),
          str(a.get('start_date') or ''),str(a.get('end_date') or ''),f'{a.get("progress",0)}%'] for a in content.get('actions',[])]
    story.extend([para('Actions and tasks','A3Block'),_table(rows,width-2*margin,[.08,.44,.18,.1,.1,.1])])
    story.extend([Spacer(1,6),para('Review gates','A3Block'),_table([['Phase','Gate','Met']]+[[g['phase'],para(g['label'],'A3Small'),'Yes' if g['ok'] else 'No'] for g in gates],width-2*margin,[.12,.76,.12])])
    if content.get('team'): story.extend([Spacer(1,6),para('Team','A3Block'),_table([['Name','Kaizen role']]+[[m['name'],m['role']] for m in content['team']],width-2*margin,[.5,.5])])
    if content.get('feedback'):
        story.extend([Spacer(1,6),para('Sensei feedback','A3Block'),_table([['Phase','Type','Feedback','Resolved']]+[[f['stage'],f['kind'],para(f['text'],'A3Small'),'Yes' if f['resolved'] else 'No'] for f in content['feedback']],width-2*margin,[.1,.12,.66,.12])])
    worksheets=[w for w in content.get('worksheets',[]) if w.get('include_in_a3') and w['method'] in REGISTRY]
    for w in worksheets:
        story.extend([PageBreak(),para(w['title'],'A3Title'),para(f'{w["stage"]} · schema v{w["schema_version"]} · worksheet r{w["revision"]}','A3Small')])
        analysis=calculate(w['method'],w['payload'])
        for message in analysis['messages']: story.append(para(message))
        story.append(para(analysis['formula'],'A3Small'))
        drawing=svg2rlg(BytesIO(render_svg(w['method'],w['payload']).encode('utf-8')))
        if drawing:
            factor=min((width-2*margin-10)/drawing.width,(height-250)/drawing.height,1)
            # Very large diagrams stay readable: list every active row instead of shrinking the labels away.
            if factor<.45:
                story.append(para('Full diagram exceeds a readable scale on this paper. Every active row is listed below; the SVG is in the archive.'))
                fields=REGISTRY[w['method']]['fields']
                for row in [r for r in w['payload']['rows'] if not r.get('archived')]:
                    story.append(para(' · '.join(f'{f["label"]}: {row.get(f["key"],"")}' for f in fields),'A3Small'))
            else:
                drawing.scale(factor,factor);drawing.width*=factor;drawing.height*=factor;story.append(drawing)
        conclusion=w['payload'].get('conclusion','')
        story.extend([Spacer(1,8),para('Conclusion / next test','A3Block'),para(conclusion or 'Not recorded'),para('Method source: '+REGISTRY[w['method']]['source'],'A3Small')])
        if w['method']=='5s' and photo_bytes:
            for row in w['payload'].get('rows',[]):
                if row.get('archived'):continue
                for key,label in [('before_attachment','Before'),('after_attachment','After')]:
                    identifier=str(row.get(key,''))
                    if identifier in photo_bytes:
                        image=Image(BytesIO(photo_bytes[identifier]));factor=min(450/image.imageWidth,240/image.imageHeight,1);image.drawWidth=image.imageWidth*factor;image.drawHeight=image.imageHeight*factor
                        story.append(KeepTogether([para(f'{row.get("pillar","")} · {label} photo (attachment #{identifier})','A3Block'),image]))
    return story

def build_pdf_many(items,paper='A3',title='TCA Progress report',label=None):
    """items: (content, photos, final) per event, each starting on a new page."""
    paper=paper if paper in PAPERS else 'A3'
    output=BytesIO();width,height=PAPERS[paper];margin=24 if paper=='A4' else 32;styles=_styles(paper)
    doc=SimpleDocTemplate(output,pagesize=(width,height),rightMargin=margin,leftMargin=margin,topMargin=margin,bottomMargin=margin+10,title=title)
    story=[]
    for index,(content,photos,final) in enumerate(items):
        if index: story.append(PageBreak())
        story.extend(_event_story(content,photos,paper,final,styles))
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(MUTED)
        canvas.drawString(margin,14,label or 'TCA Progress · synthetic/local pilot · complete archive retained')
        canvas.drawRightString(width-margin,14,f'Page {doc.page}')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()

def build_pdf(content,photo_bytes=None,paper='A3',final=True):
    label=f'TCA Progress · synthetic/local pilot · KZ-{content["event_id"]} r{content["event_revision"]} · {"finalised version" if final else "working copy"} · complete archive retained'
    return build_pdf_many([(content,photo_bytes,final)],paper,f'TCA Progress {paper} · {content["title"]}',label)

def _table(rows,total,fractions):
    table=Table(rows,colWidths=[total*f for f in fractions],repeatRows=1,hAlign='LEFT')
    table.setStyle(TableStyle([('FONTSIZE',(0,0),(-1,-1),8),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('TEXTCOLOR',(0,0),(-1,0),NAVY),
        ('LINEBELOW',(0,0),(-1,0),.8,NAVY),('LINEBELOW',(0,1),(-1,-1),.3,LINE),('VALIGN',(0,0),(-1,-1),'TOP')]))
    return table

def _photos(event):
    photos={}
    for item in event.attachments.filter(classification='internal'):
        file=item.file;name=item.original_name
        if item.evidence and item.evidence.site_id==event.site_id and item.evidence.classification=='internal':file=item.evidence.file;name=file.name if file else ''
        if file and Path(name).suffix.lower() in ('.png','.jpg','.jpeg'):
            with file.open('rb') as stream:photos[str(item.pk)]=stream.read()
    return photos

def frozen_content(event):
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    return json.loads(json.dumps(report_snapshot(event),cls=DjangoJSONEncoder))

def working_pdf(event,paper='A3'):
    """Unstored PDF of the current saved revision, clearly marked as a working copy."""
    return build_pdf(frozen_content(event),_photos(event),paper,final=False)

def ensure_report(event,user,paper='A3'):
    """Event is locked by caller; reports are immutable at each finalization revision and paper."""
    existing=event.a3_reports.filter(event_revision=event.revision,renderer_version=RENDERER_VERSION,paper=paper).first()
    if existing:return existing
    content=frozen_content(event)
    raw=build_pdf(content,_photos(event),paper);version=(event.a3_reports.order_by('-version').values_list('version',flat=True).first() or 0)+1
    report=A3Report(event=event,event_revision=event.revision,renderer_version=RENDERER_VERSION,paper=paper,version=version,snapshot=content,sha256=hashlib.sha256(raw).hexdigest(),created_by=user)
    report.file.save(f'kaizen-{event.pk}-{paper.lower()}-v{version}.pdf',ContentFile(raw),save=False);report.save();return report

def report_bytes(report):
    """Stored PDF bytes. If the file store was wiped (e.g. a free demo host restarted), the identical
    finalised layout is rebuilt from the frozen snapshot kept in the database; the hash is not reused."""
    try:
        with report.file.open('rb') as handle: return handle.read()
    except (FileNotFoundError,OSError,ValueError):
        return build_pdf(report.snapshot,None,report.paper,final=True)

def ensure_reports(event,user):
    """Finalization stores both paper versions of the same frozen revision."""
    return [ensure_report(event,user,paper) for paper in PAPERS]
