"""Escaped SVG from saved structured data, with table/list alternatives in the UI."""
from html import escape
import textwrap
from collections import defaultdict
from .toolbox_registry import REGISTRY
from .toolbox_math import calculate, number

BLUE='#2458a6';ORANGE='#b45309';NAVY='#0B1A48'
def text(x,y,value,size=14,color=NAVY):
    return f'<text x="{x:g}" y="{y:g}" font-family="Arial, sans-serif" font-size="{size}" fill="{color}">{escape(str(value))}</text>'
def line(x1,y1,x2,y2,color=BLUE,dash=False):
    return f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" stroke-width="2"'+(' stroke-dasharray="5 4"' if dash else '')+'/>'
def wrapped(x,y,value,width=34,size=13):
    lines=[]
    for para in str(value).splitlines() or ['']:
        lines.extend(textwrap.wrap(para,width,break_long_words=True) or [''])
    return ''.join(text(x,y+i*(size+4),s,size) for i,s in enumerate(lines)),len(lines)*(size+4)
def legend(x,y,items,width=110,size=12):
    """Numbered keys for in-chart markers; full labels wrap below the plot instead of overlapping it."""
    body='';h=0
    for number,label in items:
        value,lh=wrapped(x,y+h,f'{number}. {label}',width,size);body+=value;h+=lh+4
    return body,h
def fit_text(x,y,value,size,width):
    """Label beside a marker, flipped to the left when it would leave the drawing."""
    estimate=len(str(value))*size*.55
    return text(x+6 if x+6+estimate<=width-8 else max(4,x-6-estimate),y,value,size)
def short(value,limit=24):
    value=str(value);return value if len(value)<=limit else value[:limit-1]+'…'
def svg_shell(name,body,width,height):
    return f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(name)}" viewBox="0 0 {width} {height}" width="{width}" height="{height}"><title>{escape(name)}</title><rect width="100%" height="100%" fill="white"/>{body}</svg>'

def render_svg(key,payload):
    spec=REGISTRY[key];result=calculate(key,payload);rows=result['rows'];kind=spec['visual']
    if result.get('incomplete'):
        value='; '.join(result['messages']);body,h=wrapped(25,35,value,90)
        return svg_shell(spec['name'],body,960,max(100,h+55))
    if kind=='fishbone':
        categories=payload.get('meta',{}).get('categories','').splitlines()
        for r in rows:
            if r.get('category','Uncategorized') not in categories: categories.append(r.get('category','Uncategorized'))
        categories=[c for c in categories if c.strip()] or ['Uncategorized']
        groups={c:[r for r in rows if r.get('category','Uncategorized')==c] for c in categories}
        blocks={};maxh=80
        for c,items in groups.items():
            contents=[];h=24
            for r in items:
                label=('Subcause: ' if r.get('parent') else '')+r.get('cause','')+' ['+r.get('state','hypothesis')+']'
                _,rh=wrapped(0,0,label,28);contents.append((label,rh));h+=rh+8
            blocks[c]=(contents,h);maxh=max(maxh,h)
        columns=(len(categories)+1)//2;width=max(1000,columns*270+250);height=maxh*2+160;spine=maxh+75
        body=line(30,spine,width-220,spine)+text(width-215,spine-18,'Effect',16)
        effect,eh=wrapped(width-215,spine+5,payload.get('meta',{}).get('effect','Effect not entered'),24)
        body+=effect
        height=max(height,spine+eh+35)
        for i,c in enumerate(categories):
            col=i//2;top=i%2==0;x=45+col*270;y=42 if top else spine+60
            body+=line(x+120,y+10,x+220,spine)+text(x,y,c,16)
            y+=24
            for label,rh in blocks[c][0]:
                value,_=wrapped(x,y,label,28);body+=value;y+=rh+8
        return svg_shell(spec['name'],body,width,height)
    if kind=='yamazumi' and result.get('series'):
        series=result['series'];maximum=max([s['value'] for s in series]+[result['takt'],1]);body='';width=max(900,len(series)*180+120)
        colors=[BLUE,ORANGE,'#047857','#7c3aed'];baseline=330
        for i,station in enumerate(series):
            x=100+i*180;y=baseline
            for j,row in enumerate(r for r in rows if r['operator']==station['label']):
                h=number(row['time'])/maximum*270;y-=h;body+=f'<rect x="{x}" y="{y}" width="110" height="{h}" fill="{colors[j%4]}"/>'
            label,_=wrapped(x,365,station['label'],18);body+=label+text(x,baseline-station['value']/maximum*270-12,f'{station["value"]:g}',13)
        ty=baseline-result['takt']/maximum*270;body+=line(50,ty,width-25,ty,ORANGE,True)+text(50,ty-8,f'Takt {result["takt"]:g} {result["unit"]}',13,ORANGE)
        return svg_shell(spec['name'],body,width,450)
    if kind=='relations':
        nodes=list(dict.fromkeys([r.get(f,'') for r in rows for f in ('from','to') if r.get(f)]));body='';positions={};y=45
        for name in nodes:
            label,h=wrapped(40,y,name,48);positions[name]=(470,y-5);body+=label;y+=max(50,h+15)
        for i,r in enumerate(rows):
            if r.get('from') not in positions or r.get('to') not in positions: continue
            x1,y1=positions[r['from']];x2,y2=positions[r['to']];offset=500+i*25
            body+=f'<path d="M{x1},{y1} L{offset},{y1} L{offset},{y2} L{x2},{y2}" fill="none" stroke="{BLUE}" stroke-width="2"/>'+f'<polygon points="{x2},{y2} {x2+8},{y2-5} {x2+8},{y2+5}" fill="{BLUE}"/>'
        return svg_shell(spec['name'],body,max(950,550+len(rows)*25),max(180,y+20))
    if kind in ('affinity','5s','heijunka'):
        groups=defaultdict(list)
        if key=='affinity':
            for name in payload.get('meta',{}).get('groups','').splitlines():
                if name.strip(): groups[name]=[]
        for r in rows: groups[r.get('group') or r.get('pillar') or r.get('slot') or r.get('status') or 'Ungrouped'].append(r)
        body='';x=30;maxy=100
        for group,items in groups.items():
            body+=text(x,30,group,16);y=62
            for r in items:
                value=' · '.join(f'{f["label"]}: {r.get(f["key"])}' for f in spec['fields'] if r.get(f['key']) not in ('',None))
                label,h=wrapped(x+12,y+4,value,30);body+=f'<rect x="{x}" y="{y-18}" width="270" height="{h+32}" rx="6" fill="#eff4fa" stroke="{BLUE}"/>'+label;y+=h+55
            maxy=max(maxy,y);x+=300
        return svg_shell(spec['name'],body,max(900,x+20),maxy+20)
    if kind in ('pareto','bars','histogram','takt','oee') and result.get('series'):
        series=result['series'];maxvalue=max([abs(s['value']) for s in series]+[result.get('takt',0),1]);body=text(275,24,f'Value ({result.get("unit","local metric")}); scale 0 to {maxvalue:g}',13)
        y=60;points=[]
        for item in series:
            label,h=wrapped(20,y,item['label'],29);barwidth=600*abs(item['value'])/maxvalue
            body+=label+f'<rect x="275" y="{y-13}" width="{barwidth}" height="18" fill="{BLUE}"/>'+text(890,y,f'{item["value"]:g}',13)
            if item.get('cumulative') is not None:
                px=275+600*item['cumulative']/100;points.append((px,y-4));body+=f'<circle cx="{px}" cy="{y-4}" r="4" fill="{ORANGE}"/>'+text(1000,y,f'{item["cumulative"]:.1f}%',13,ORANGE)
            if item.get('limit') is not None: body+=line(275+600*item['limit']/maxvalue,y-15,275+600*item['limit']/maxvalue,y+5,ORANGE)
            if item.get('after') is not None: body+=text(890,y+18,f'Proposed {item["after"]:g}',12)
            y+=max(45,h+12)
        if points: body+=f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" fill="none" stroke="{ORANGE}" stroke-width="2"/>'+line(755,36,755,y,ORANGE,True)+text(275,y+15,'Orange: cumulative 0–100%; dashed reference 80%',13,ORANGE)
        if result.get('takt') is not None:
            tx=275+600*result['takt']/maxvalue;body+=line(tx,35,tx,y,ORANGE,True)+text(275,y+15,f'Reference takt {result["takt"]:g}',13,ORANGE)
        return svg_shell(spec['name'],body,1130,y+50)
    if kind in ('run','control','scatter','matrix','boxplot','spaghetti'):
        width=1000;height=440;body=line(70,350,940,350)+line(70,35,70,350)
        if kind in ('run','control'):
            series=result['series'];values=[s['value'] for s in series];lo=min(values+[result.get('lcl',min(values))]);hi=max(values+[result.get('ucl',max(values))]);span=hi-lo or 1
            coords=[(70+i*860/max(1,len(series)-1),350-(s['value']-lo)/span*290) for i,s in enumerate(series)]
            body+=f'<polyline points="{" ".join(f"{x},{y}" for x,y in coords)}" fill="none" stroke="{BLUE}" stroke-width="2"/>'
            for x,y in coords: body+=f'<circle cx="{x}" cy="{y}" r="3" fill="{BLUE}"/>'
            for label,value in ([('LCL',result['lcl']),('Mean',result['center']),('UCL',result['ucl'])] if kind=='control' else [('Median',result['median'])]):
                sy=350-(value-lo)/span*290;body+=line(70,sy,930,sy,ORANGE,True)+text(75,sy-5,f'{label} {value:g}',12,ORANGE)
            body+=text(70,385,f'Ordered observations 1–{len(series)} ({result.get("unit","")}); full periods in source table.',13)
            if kind=='control':
                mr=result['moving_ranges'];upper=max(result['mr_ucl'],max(mr),1);my=730
                body+=text(70,445,'Moving range (consecutive span 2)',16)+line(70,my,940,my)
                pts=[(70+i*860/max(1,len(mr)-1),my-v/upper*220) for i,v in enumerate(mr)]
                body+=f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{BLUE}" stroke-width="2"/>'
                for label,value in [('MR mean',result['mr_center']),('MR UCL',result['mr_ucl'])]:
                    sy=my-value/upper*220;body+=line(70,sy,940,sy,ORANGE,True)+text(75,sy-5,f'{label} {value:g}',12,ORANGE)
                height=780
        elif kind in ('scatter','matrix'):
            points=result['points'];xs=[p['x'] for p in points];ys=[p['y'] for p in points];xmin=min(xs) if kind=='scatter' else 1;xmax=max(xs) if kind=='scatter' else 5;ymin=min(ys) if kind=='scatter' else 1;ymax=max(ys) if kind=='scatter' else 5
            for index,p in enumerate(points,1):
                x=70+(p['x']-xmin)/(xmax-xmin or 1)*860;y=350-(p['y']-ymin)/(ymax-ymin or 1)*290
                body+=f'<circle cx="{x}" cy="{y}" r="6" fill="{BLUE}"/>'+fit_text(x+2,y-5,str(index),12,width)
            body+=text(70,385,f'X {xmin:g} to {xmax:g} · Y {ymin:g} to {ymax:g}',13)
            if kind=='matrix': body+=line(500,35,500,350,ORANGE,True)+line(70,205,940,205,ORANGE,True)+text(70,415,'Local scale: X effort, Y impact. Midpoint is a discussion aid.',13)
            keys,kh=legend(70,445,[(i,p['label']) for i,p in enumerate(points,1)],120);body+=keys;height=max(height,460+kh)
        elif kind=='boxplot':
            series=result['series'];lo=min(s['low'] for s in series);hi=max(s['high'] for s in series)
            lo=min([lo]+[v for s in series for v in s['outliers']]);hi=max([hi]+[v for s in series for v in s['outliers']]);span=hi-lo or 1
            body='';rows_y=[];y=55
            for s in series:
                _,lh=wrapped(15,0,s['label'],34);rows_y.append(y);y+=max(90,lh+50)
            height=max(220,y+20)
            for i,s in enumerate(series):
                y=rows_y[i];scale=lambda v:300+(v-lo)/span*600
                label,_=wrapped(15,y,s['label'],34)
                body+=label+line(scale(s['low']),y,scale(s['high']),y)+f'<rect x="{scale(s["q1"])}" y="{y-15}" width="{max(1,scale(s["q3"])-scale(s["q1"]))}" height="30" fill="#c9d8ed" stroke="{BLUE}"/>'+line(scale(s['median']),y-15,scale(s['median']),y+15,ORANGE)
                body+=text(300,y+35,f'n={s["n"]}; median {s["median"]:g}; Q1 {s["q1"]:g}; Q3 {s["q3"]:g}',12)
                for v in s['outliers']: body+=f'<circle cx="{scale(v)}" cy="{y}" r="4" fill="{ORANGE}"/>'
        else:
            routes=result['routes'];xs=[number(r['x']) for route in routes for r in route['points']];ys=[number(r['y']) for route in routes for r in route['points']];lo=min(xs);bot=min(ys);sx=max(xs)-lo or 1;sy=max(ys)-bot or 1
            for i,route in enumerate(routes):
                color=BLUE if i%2==0 else ORANGE;coords=[(70+(number(p['x'])-lo)/sx*860,350-(number(p['y'])-bot)/sy*290) for p in route['points']]
                body+=f'<polyline points="{" ".join(f"{x},{y}" for x,y in coords)}" fill="none" stroke="{color}" stroke-width="2"/>'
                for (x,y),p in zip(coords,route['points']): body+=f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>'+fit_text(x,y-7,short(p.get('point',''),18),12,width)
                body+=text(70,385+i*20,f'{route["label"]}: {route["distance"]:g} {rows[0]["unit"]}',13,color)
            height=max(height,410+len(routes)*20)
            long=[(f'{route["label"]}',p.get('point','')) for route in routes for p in route['points'] if len(str(p.get('point','')))>18]
            if long:
                keys,kh=legend(70,height+10,[(label,point) for label,point in long],120);body+=keys;height+=kh+20
        return svg_shell(spec['name'],body,width,height)
    # Flow, trees, affinity boards and operational plans: generated labeled blocks
    # retain every active row. Connections reference row IDs; list alternatives
    # include all fields. No user-authored SVG/HTML is accepted.
    body='';y=35;positions={};blocks=[]
    for i,row in enumerate(rows):
        group=row.get('group') or row.get('pillar') or row.get('lane') or row.get('state') or row.get('branch') or 'Ungrouped'
        value=' · '.join(f'{f["label"]}: {row.get(f["key"])}' for f in spec['fields'] if row.get(f['key']) not in ('',None))
        contents,h=wrapped(55,y+22,value,98);height=max(60,h+42)
        blocks.append(f'<rect x="35" y="{y-18}" width="870" height="{height}" rx="8" fill="#eff4fa" stroke="{BLUE}"/>'+text(55,y,f'{i+1}. {group}',14)+contents)
        positions[row['id']]=(940,y+height/2);y+=height+25
    for i,row in enumerate(rows):
        parent=row.get('parent')
        targets=row.get('next','').split(',') if kind=='flow' else []
        if parent in positions: targets.append(parent)
        if not targets and kind in ('flow','vsm') and i+1<len(rows): targets=[rows[i+1]['id']]
        for target in targets:
            target=target.strip()
            if target in positions:
                x1,y1=positions[row['id']];x2,y2=positions[target];body+=line(x1,y1,x2,y2,ORANGE)+f'<circle cx="{x2}" cy="{y2}" r="4" fill="{ORANGE}"/>'
    body+=''.join(blocks)
    return svg_shell(spec['name'],body,1000,max(120,y+15))
