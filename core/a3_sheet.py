"""First-page report sheets that follow the Global Kaizen template report tabs.

A3 follows the LANDSCAPE tab (header grid; PLAN on the left; DO, CHECK and ACT on the right; site
manager comments at the bottom). A4 follows the PORTRAIT tab (the same sections stacked in one column).
Like the template, the sheet lists the first five key actions per phase and cuts long text; this
renderer marks every cut and repeats the full wording under "Complete content". Values are read from
the saved event; the workbook formulas themselves are not recalculated.
"""
from datetime import date
from html import escape
from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

NAVY=colors.HexColor('#0B1A48');MUTED=colors.HexColor('#4B5265');LINE=colors.HexColor('#D8DBE3')
BAND=colors.HexColor('#E8EBF4');GREEN=colors.HexColor('#2F7D45');GREY=colors.HexColor('#9AA1B2');RED=colors.HexColor('#E4002B')
CUT='[Summary shortened; continues under "Complete content"]'

def header_fields(event,team):
    """Template header (LANDSCAPE!B2:EG10) from the saved event; empty template values stay empty."""
    data=event.data
    dates=[a.start_date for a in event.actions.all() if a.start_date]
    ends=[a.end_date for a in event.actions.all() if a.end_date]
    lead=next((m['name'] for m in team if m['role']=='Kaizen lead'),'')
    coach=next((m['name'] for m in team if m['role']=='Sensei'),'')
    from .methodology import rules_for
    return [('KAIZEN TITLE',event.title),('KAIZEN TYPE',rules_for(event.profile)['label']),
            ('START DATE',data.get('coach_28') or (min(dates).isoformat() if dates else event.created_at.date().isoformat())),
            ('END DATE',data.get('coach_29') or data.get('due_date') or (max(ends).isoformat() if ends else '')),
            ('BUSINESS UNIT',data.get('coach_22','')),('CONTRACT ID',data.get('coach_21','')),('LOCATION ID',data.get('coach_20','')),
            ('COUNTRY',data.get('coach_19') or event.site.get_country_code_display()),('PROBLEM TYPE',data.get('coach_48','')),('BUSINESS TYPE',data.get('coach_25','')),
            ('KAIZEN LEADER',data.get('coach_31') or lead or data.get('owner','')),('KAIZEN COACH',data.get('coach_33') or coach),('TEAM NAME',event.site.name),
            ('TEAM MEMBERS',', '.join(m['name'] for m in team))]

def _cut(value,limit):
    value=str(value or '').strip()
    if len(value)<=limit: return value,False
    return value[:limit].rsplit(' ',1)[0]+' … '+CUT,True

def _trend(points,target,width,height,colour,label):
    """Small run chart of one phase's observations with a dashed target line, as the template trend boxes."""
    drawing=Drawing(width,height)
    drawing.add(Rect(0,0,width,height,fillColor=colors.white,strokeColor=LINE,strokeWidth=.6))
    drawing.add(String(6,height-11,label,fontName='Helvetica-Bold',fontSize=7,fillColor=MUTED))
    values=[v for _,v in points]
    if not values:
        drawing.add(String(6,height/2-4,'No observations recorded',fontName='Helvetica',fontSize=7,fillColor=MUTED));return drawing
    span=values+([target] if target is not None else [])
    lo=min(span);hi=max(span)
    if hi==lo: lo,hi=lo-1,hi+1
    left,bottom,plot_w,plot_h=26,12,width-34,height-30
    y=lambda v: bottom+(v-lo)/(hi-lo)*plot_h
    x=lambda i: left+(plot_w*(i/(len(values)-1)) if len(values)>1 else plot_w/2)
    drawing.add(Line(left,bottom,left+plot_w,bottom,strokeColor=LINE,strokeWidth=.6))
    drawing.add(String(2,y(hi)-3,f'{hi:g}',fontName='Helvetica',fontSize=6,fillColor=MUTED))
    drawing.add(String(2,y(lo)-3,f'{lo:g}',fontName='Helvetica',fontSize=6,fillColor=MUTED))
    if target is not None:
        drawing.add(Line(left,y(target),left+plot_w,y(target),strokeColor=RED,strokeWidth=.8,strokeDashArray=[3,2]))
    coords=[c for i,v in enumerate(values) for c in (x(i),y(v))]
    if len(values)>1: drawing.add(PolyLine(coords,strokeColor=colour,strokeWidth=1.4))
    for i,v in enumerate(values): drawing.add(Rect(x(i)-1.6,y(v)-1.6,3.2,3.2,fillColor=colour,strokeColor=None))
    return drawing

def _num(value):
    try: return float(value)
    except (TypeError,ValueError): return None

def result_facts(content):
    """CURRENT / TARGET / AFTER / IMPROVEMENT and 'Was the target achieved?' (CHECK!K32 is not stored)."""
    data=content['data'];comparison=next((c for c in content.get('comparisons',[]) if c.get('difference') is not None),None)
    before=_num(data.get('baseline')) if _num(data.get('baseline')) is not None else _num(comparison and comparison['before_average'])
    after=_num(data.get('actual')) if _num(data.get('actual')) is not None else _num(comparison and comparison['after_average'])
    target=_num(data.get('target'));unit=data.get('unit') or (comparison or {}).get('unit','')
    improvement=None if before is None or after is None else after-before
    achieved='Not determined'
    if target is not None and after is not None and data.get('direction') in ('up','down'):
        achieved='Yes' if (after>=target if data['direction']=='up' else after<=target) else 'No'
    measure=data.get('measure') or (comparison or {}).get('measure','')
    obs=[o for o in content.get('observations',[]) if not measure or o.get('measure')==measure]
    series=lambda phase:[(o.get('period_start'),_num(o['value'])) for o in sorted(obs,key=lambda o:(str(o.get('period_start')),o.get('id',0))) if o['phase']==phase and _num(o['value']) is not None]
    fmt=lambda v: '' if v is None else f'{v:g} {unit}'.strip()
    pct='' if improvement is None or not before else f' ({improvement/before*100:+.0f}%)'
    return {'measure':measure,'before':fmt(before),'after':fmt(after),'target':fmt(target),'improvement':(f'{improvement:+g} {unit}'.strip()+pct) if improvement is not None else '',
            'achieved':achieved,'before_series':series('before'),'after_series':series('after'),'target_value':target}

def template_sheet(content,paper,final,styles,width,margin):
    """Returns (flowables, shortened) for the first page."""
    data=content['data'];inner=width-2*margin;shortened=[False]
    def p(value,style='Cell'):
        return Paragraph(escape(str(value or '')).replace('\n','<br/>'),styles[style])
    def cut(value,limit):
        text,was=_cut(value,limit);shortened[0]=shortened[0] or was;return text
    small=paper=='A4'
    limit=lambda big,a4: a4 if small else big
    # --- header grid
    fields=content.get('header',[])
    pairs=[[p(label,'Label'),p(cut(value,90),'Cell')] for label,value in fields]
    if small:
        rows=[pairs[i]+(pairs[i+1] if i+1<len(pairs) else ['','']) for i in range(0,len(pairs)-1,2)]
        if len(pairs)%2: rows[-1]=pairs[-1]+['','']
        header=Table(rows,colWidths=[inner*.17,inner*.33,inner*.17,inner*.33])
    else:
        body=pairs[:-1];rows=[sum(body[i:i+3],[]) for i in range(0,len(body),3)]
        rows=[r+['']*(6-len(r)) for r in rows]+[pairs[-1]+['']*4]
        header=Table(rows,colWidths=[inner*.09,inner*.24,inner*.09,inner*.24,inner*.09,inner*.25])
        header.setStyle(TableStyle([('SPAN',(1,len(rows)-1),(5,len(rows)-1))]))
    header.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,LINE),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BACKGROUND',(0,0),(0,-1),BAND),
        ('BACKGROUND',(2,0),(2,-1 if small else -3),BAND),*([('BACKGROUND',(4,0),(4,-3),BAND)] if not small else []),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
    facts=result_facts(content)
    plan_qa=[('WHAT IS THE CURRENT SITUATION THAT YOU ARE LOOKING TO IMPROVE/RESOLVE?',data.get('overall_problem')),
             ('WHY IS IT IMPORTANT TO FIX THIS PROBLEM?',data.get('fivew2h_why')),('IN WHICH AREA DOES THE PROBLEM OCCUR?',data.get('coach_49') or data.get('process_location')),
             ('IN WHICH PROCESS DOES THE PROBLEM OCCUR?',data.get('coach_50')),('WHO DOES THE PROBLEM INVOLVE?',data.get('fivew2h_who')),
             ('WHEN DOES THE PROBLEM OCCUR?',data.get('fivew2h_when')),('WHAT KIND OF PRODUCT/SERVICE IS INVOLVED?',data.get('fivew2h_what'))]
    def actions(phase):
        rows=[a for a in content.get('actions',[]) if a['phase']==phase][:5]
        out=[[p('#','Label'),p('KEY ACTIONS TO MITIGATE THE ROOT CAUSE' if phase=='DO' else 'KEY ACTIONS TO SUSTAIN & FURTHER IMPROVE ON THE CHANGES MADE','Label'),p('OWNER','Label'),p("DUR' (DAYS)",'Label')]]
        for i,a in enumerate(rows,1):
            days=''
            try: days=str((date.fromisoformat(str(a['end_date']))-date.fromisoformat(str(a['start_date']))).days) if a.get('start_date') and a.get('end_date') else ''
            except ValueError: pass
            out.append([p(i),p(cut(a['description'],200)),p(a.get('assignee_name') or a.get('owner','')),p(days)])
        extra=len([a for a in content.get('actions',[]) if a['phase']==phase])-len(rows)
        if extra>0: shortened[0]=True;out.append(['',p(f'+{extra} more · {CUT}','Small'),'',''])
        if len(out)==1: out.append(['',p('No actions recorded','Small'),'',''])
        return out
    def box(title,value,lim):
        return [p(title,'Label'),p(cut(value,lim) or 'Not recorded')]
    def band(text): return p(text,'Band')
    def grid(rows,widths,style=()):
        t=Table(rows,colWidths=widths);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,LINE),
            ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),3),*style]));return t
    half=inner if small else (inner-10)/2
    chart_w=half if not small else (inner-8)/2;chart_h=limit(170,80)
    before_chart=_trend(facts['before_series'],facts['target_value'],chart_w,chart_h,GREY,'BEFORE - TREND OF THE LOCAL MEASURE')
    after_chart=_trend(facts['after_series'],facts['target_value'],chart_w,chart_h,GREEN,'AFTER - TREND OF THE LOCAL MEASURE')
    qa=grid([[p(q,'Label'),p(cut(a,limit(260,180)) or 'Not recorded')] for q,a in plan_qa],[half*.45,half*.55],[('BACKGROUND',(0,0),(0,-1),BAND)])
    specific=grid([box('SPECIFIC MAIN PROBLEM',data.get('specific_problem'),limit(500,300))],[half*.3,half*.7],[('BACKGROUND',(0,0),(0,-1),BAND)])
    measure=p((facts['measure']+' - TREND') if facts['measure'] else 'LOCAL MEASURE - TREND','Label')
    numbers=grid([[p('CURRENT','Label'),p(facts['before']),p('TARGET','Label'),p(facts['target'])]],[half*.2,half*.3,half*.2,half*.3],[('BACKGROUND',(0,0),(0,0),BAND),('BACKGROUND',(2,0),(2,0),BAND)])
    cause=grid([box('CAUSE ANALYSIS - SPECIFIC ROOT CAUSE',data.get('root_cause'),limit(500,300))],[half*.3,half*.7],[('BACKGROUND',(0,0),(0,-1),BAND)])
    plan=[band('PLAN'),qa,Spacer(1,4),specific,Spacer(1,4),measure,before_chart,numbers,Spacer(1,4),cause]
    solution=grid([box('SOLUTION AREA',data.get('coach_60'),120),box('SOLUTION PROCESS',data.get('coach_61'),120),box('SPECIFIC SOLUTION',data.get('solution'),limit(600,350))],
                  [half*.3,half*.7],[('BACKGROUND',(0,0),(0,-1),BAND)])
    widths=[half*.06,half*.62,half*.2,half*.12]
    do=[band('DO'),solution,Spacer(1,4),grid(actions('DO'),widths,[('BACKGROUND',(0,0),(-1,0),BAND)])]
    check=[band('CHECK'),after_chart,grid([[p('AFTER','Label'),p(facts['after']),p('IMPROVEMENT','Label'),p(facts['improvement'])],
                                          [p('WAS THE TARGET ACHIEVED?','Label'),p(facts['achieved']),'','']],[half*.2,half*.3,half*.2,half*.3],
                                         [('BACKGROUND',(0,0),(0,-1),BAND),('BACKGROUND',(2,0),(2,0),BAND),('SPAN',(1,1),(3,1))])]
    act=[band('ACT'),grid(actions('ACT'),widths,[('BACKGROUND',(0,0),(-1,0),BAND)])]
    comments=grid([[p("SITE MANAGER'S COMMENTS",'Label'),p(cut(data.get('coach_35') or '',300) or 'Not recorded')]],[inner*.18,inner*.82],[('BACKGROUND',(0,0),(0,-1),BAND)])
    title=[p(content['title'],'SheetTitle'),p(f'{content["site"]} · KZ-{content["event_id"]} · revision {content["event_revision"]} · input view {content["input_profile"]} · review state {content.get("review_state","")} · {paper} {"portrait" if small else "landscape"} · layout after the Global Kaizen template {"PORTRAIT" if small else "LANDSCAPE"} tab','Small')]
    from .a3 import LOGO
    story=[]
    if LOGO.exists():
        top=Table([[Image(str(LOGO),width=72,height=25,mask='auto'),title]],colWidths=[86,inner-86]);top.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0)]));story.append(top)
    else: story.extend(title)
    if not final: story.append(p('WORKING COPY · not a finalised report version. Values are shown as saved at this revision.','Banner'))
    story.extend([Spacer(1,4),header,Spacer(1,6)])
    if small:
        charts=Table([[before_chart,after_chart]],colWidths=[chart_w+4,chart_w+4]);charts.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0)]))
        plan=[band('PLAN'),qa,Spacer(1,3),specific,Spacer(1,3),cause,Spacer(1,3),measure,charts,numbers]
        check=[band('CHECK'),grid([[p('AFTER','Label'),p(facts['after']),p('IMPROVEMENT','Label'),p(facts['improvement'])],[p('WAS THE TARGET ACHIEVED?','Label'),p(facts['achieved']),'','']],
                                  [inner*.2,inner*.3,inner*.2,inner*.3],[('BACKGROUND',(0,0),(0,-1),BAND),('BACKGROUND',(2,0),(2,0),BAND),('SPAN',(1,1),(3,1))])]
        story.extend(plan+[Spacer(1,5)]+do+[Spacer(1,5)]+check+[Spacer(1,5)]+act+[Spacer(1,5),comments])
    else:
        body=Table([[plan,do+[Spacer(1,6)]+check+[Spacer(1,6)]+act]],colWidths=[half+5,half+5])
        body.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(0,0),10),('RIGHTPADDING',(1,0),(1,0),0)]))
        story.extend([body,Spacer(1,6),comments])
    return story,shortened[0]
