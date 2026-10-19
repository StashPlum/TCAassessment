"""Pure worksheet validation/calculations; shared by pages, SVG and reports."""
import math
import statistics as stats
from collections import defaultdict
from copy import deepcopy
from .toolbox_registry import REGISTRY

def number(value):
    try: result=float(value)
    except (TypeError,ValueError): raise ValueError('Enter a numeric value.')
    if not math.isfinite(result) or abs(result)>1e15: raise ValueError('Enter a finite numeric value within ±10^15.')
    return result

def validate_payload(key,payload):
    if key not in REGISTRY: raise ValueError('Unknown method.')
    if not isinstance(payload,dict) or not isinstance(payload.get('meta',{}),dict) or not isinstance(payload.get('rows'),list):
        raise ValueError('Worksheet must contain metadata and structured rows.')
    ids=[];spec=REGISTRY[key]
    for field in spec['meta']:
        val=payload.get('meta',{}).get(field['key'],'')
        validate_cell(field,val,'Settings')
    for index,row in enumerate(payload['rows'],1):
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not row['id']: raise ValueError(f'Row {index} needs a stable ID.')
        ids.append(row['id'])
        for f in spec['fields']: validate_cell(f,row.get(f['key'],''),f'Row {index}')
        if key in ('ishikawa','5whys') and row.get('state')=='validated' and (not row.get('evidence_id') or not row.get('test',row.get('uncertainty','')).strip()):
            raise ValueError(f'Row {index}: a validated cause needs linked evidence and a validation explanation.')
        # Numerical restrictions are method-specific: signed observations are valid.
        nonnegative={'pareto':['value'],'check-sheet':['count'],'vsm':['cycle','wait','wip'],'waste':['time'],
                     'flowchart':['time'],'kanban':['wip','limit'],'takt':['cycle'],'yamazumi':['time'],
                     'smed':['before','after'],'heijunka':['quantity'],'standard-work':['time','wip'],
                     'oee':['planned','run','ideal_cycle','total','good'],'decision-matrix':['weight']}.get(key,[])
        for name in nonnegative:
            if row.get(name) not in ('',None) and number(row[name])<0: raise ValueError(f'Row {index}: {name} cannot be negative.')
        for name,low,high in ([('score',0,2)] if key=='5s' else [('impact',1,5),('effort',1,5)] if key=='impact-effort' else [('severity',1,10),('occurrence',1,10),('detection',1,10)] if key=='fmea' else []):
            if row.get(name) not in ('',None) and not low<=number(row[name])<=high: raise ValueError(f'Row {index}: {name} must be {low}–{high} on the defined local scale.')
    if len(set(ids))!=len(ids): raise ValueError('Row IDs must be unique.')
    if any(len(str(value))>100000 for row in payload['rows'] for value in row.values()): raise ValueError('A single field exceeds the 100,000 character storage limit.')
    for row in payload['rows']:
        parent=row.get('parent','')
        if parent and parent not in ids: raise ValueError('A parent must reference an existing row ID.')
        seen={row['id']};cursor=parent
        by_id={r['id']:r for r in payload['rows']}
        while cursor:
            if cursor in seen: raise ValueError('Cause / tree parents cannot form a cycle.')
            seen.add(cursor);cursor=by_id[cursor].get('parent','')
    return payload

def validate_cell(field,val,where):
    if isinstance(val,(dict,list)): raise ValueError(f'{where}: {field["label"]} must be a scalar.')
    if val in ('',None): return
    if field['type']=='number': number(val)
    if field['type']=='select' and val not in field['choices']: raise ValueError(f'{where}: choose a valid {field["label"]}.')

def quantile(values,p):
    values=sorted(values);index=(len(values)-1)*p;low=math.floor(index);high=math.ceil(index)
    return values[low]+(values[high]-values[low])*(index-low)

def uniform(rows,field='unit',selected=None):
    units={str(r.get(field,'')).strip() for r in rows}
    if len(units)!=1 or '' in units: raise ValueError(f'Use one explicit {field.replace("_"," ")} for this analysis.')
    unit=next(iter(units))
    if selected and selected!=unit: raise ValueError('Row units must match the selected unit.')
    return unit

def need(rows,*fields):
    if not rows: raise ValueError('No active data yet. Add rows to generate the analysis.')
    for i,row in enumerate(rows,1):
        if any(row.get(f) in ('',None) for f in fields): raise ValueError(f'Active row {i}: complete '+', '.join(fields)+'.')

def calculate(key,payload):
    """Invalid or incomplete analyses return a useful message; drafts remain saveable."""
    rows=[r for r in payload.get('rows',[]) if not r.get('archived')];meta=payload.get('meta',{})
    result={'rows':rows,'messages':[],'formula':'Structured worksheet; no automatic causal or approval conclusion.'}
    try:
        validate_payload(key,payload)
        if not rows: raise ValueError('No active rows yet.')
        if key in ('pareto','check-sheet'):
            val='value' if key=='pareto' else 'count';need(rows,'category',val)
            unit=uniform(rows,selected=meta.get('unit')) if key=='pareto' else 'count'
            totals=defaultdict(float)
            for r in rows: totals[r['category']]+=number(r[val])
            total=sum(totals.values());cumulative=0;values=[]
            for label,value in sorted(totals.items(),key=lambda x:(-x[1],x[0])):
                cumulative+=value;values.append({'label':label,'value':value,'cumulative':100*cumulative/total if total else None})
            result.update(series=values,total=total,unit=unit,formula='Sum per category; descending contribution; cumulative % = 100 × running sum / total.')
            if not total: result['messages'].append('Total is zero: cumulative percentages are undefined; no 100% claim.')
        elif key in ('histogram','run-chart','control-chart','boxplot','stratification'):
            need(rows,'value');unit=uniform(rows,selected=meta.get('unit'));values=[number(r['value']) for r in rows]
            result.update(unit=unit,n=len(values))
            if key=='histogram':
                bins=int(number(meta.get('bins') or 5))
                if not 1<=bins<=50: raise ValueError('Choose 1–50 equal-width bins.')
                lo=min(values);hi=max(values)
                if lo==hi: series=[{'label':str(lo),'value':len(values)}]
                else:
                    width=(hi-lo)/bins;counts=[0]*bins
                    for val in values: counts[min(bins-1,int((val-lo)/width))]+=1
                    series=[{'label':f'{lo+i*width:g} to {lo+(i+1)*width:g}'+(' inclusive' if i==bins-1 else ''),'value':n} for i,n in enumerate(counts)]
                result.update(series=series,formula='Equal-width bins; left closed/right open, final upper edge included.')
                if len(values)<50: result['messages'].append('Fewer than 50 observations: inspect representativeness; distribution is descriptive only.')
            elif key in ('run-chart','control-chart'):
                need(rows,'period')
                result.update(series=[{'label':r['period'],'value':v} for r,v in zip(rows,values)],median=stats.median(values),formula='Saved row order is measurement order; center line = median.')
                if key=='control-chart':
                    if len(values)<20: raise ValueError('I–MR requires at least 20 ordered individual continuous baseline observations in this pilot.')
                    mr=[abs(b-a) for a,b in zip(values,values[1:])];mrbar=stats.mean(mr);center=stats.mean(values)
                    result.update(center=center,lcl=center-2.66*mrbar,ucl=center+2.66*mrbar,mr_center=mrbar,mr_lcl=0,mr_ucl=3.267*mrbar,
                                  moving_ranges=mr,formula='I: mean ± 2.66 × mean moving range (span 2). MR: 0 to 3.267 × MR mean. Consecutive independent continuous values, stable baseline; limits are estimates, not specification limits.')
                    if mrbar==0: result['messages'].append('Moving range is zero: estimated limits collapse; inspect measurement resolution.')
            else:
                need(rows,'group' if key=='boxplot' else 'stratum');groups=defaultdict(list)
                for r in rows: groups[r.get('group',r.get('stratum'))].append(number(r['value']))
                summaries=[]
                for label,group in groups.items():
                    q1=quantile(group,.25);q3=quantile(group,.75);iqr=q3-q1;inside=[v for v in group if q1-1.5*iqr<=v<=q3+1.5*iqr]
                    summaries.append({'label':label,'value':stats.mean(group),'median':stats.median(group),'q1':q1,'q3':q3,'low':min(inside),'high':max(inside),'outliers':[v for v in group if v not in inside],'n':len(group)})
                result.update(series=summaries,formula='Linear-interpolation quartiles (index (n−1)p); Tukey whiskers within 1.5 IQR. Stratification shows group means and counts.')
        elif key in ('scatter','impact-effort'):
            x,y=('x','y') if key=='scatter' else ('effort','impact');need(rows,x,y)
            pairs=[(number(r[x]),number(r[y])) for r in rows]
            if key=='scatter':
                uniform(rows,'x_unit');uniform(rows,'y_unit')
                if len(pairs)<2: raise ValueError('At least two paired measurements are needed.')
                xs,ys=zip(*pairs);xm=stats.mean(xs);ym=stats.mean(ys);den=math.sqrt(sum((v-xm)**2 for v in xs)*sum((v-ym)**2 for v in ys))
                result['correlation']=sum((a-xm)*(b-ym) for a,b in pairs)/den if den else None
                if not den: result['messages'].append('Correlation is undefined when one variable has zero variance.')
            elif not meta.get('scale'): result['messages'].append('Define the local scoring anchors before using these scores to choose.')
            result.update(points=[{'x':a,'y':b,'label':r.get('option',str(i+1))} for i,((a,b),r) in enumerate(zip(pairs,rows))],formula='Pearson r for paired numeric values; no causal inference.' if key=='scatter' else 'Local 1–5 impact and effort; no official threshold.')
        elif key=='decision-matrix':
            need(rows,'option','criterion','weight','score');criteria={};options=defaultdict(dict)
            for r in rows:
                weight=number(r['weight']);criterion=r['criterion'];option=r['option']
                if criterion in criteria and criteria[criterion]!=weight: raise ValueError('Each criterion must have the same weight for every option.')
                if criterion in options[option]: raise ValueError('Each option/criterion must appear once.')
                criteria[criterion]=weight;options[option][criterion]=number(r['score'])*weight
            if sum(criteria.values())<=0: raise ValueError('Total criterion weight must be positive.')
            if any(set(scores)!=set(criteria) for scores in options.values()): raise ValueError('Every option must include every criterion.')
            result.update(series=[{'label':option,'value':sum(scores.values())/sum(criteria.values())} for option,scores in options.items()],formula='Weighted mean = sum(weight × score) / sum(weights), identical criteria and weights per option.')
            if not meta.get('scale'): result['messages'].append('Record the local scoring scale before making a decision.')
        elif key=='fmea':
            need(rows,'failure','severity','occurrence','detection')
            result.update(series=[{'label':r['failure'],'value':number(r['severity'])*number(r['occurrence'])*number(r['detection'])} for r in rows],formula='Local RPN = severity × occurrence × detection (each 1–10). RPN is not an approval or universal action threshold.')
            if not meta.get('scale'): result['messages'].append('Define local rating anchors before prioritizing.')
        elif key=='takt':
            available=number(meta.get('available'));demand=number(meta.get('demand'))
            if available<=0 or demand<=0: raise ValueError('Net available time and period demand must be positive.')
            need(rows,'cycle');unit=uniform(rows,selected=meta.get('unit'))
            if not meta.get('period'): raise ValueError('Define the shared demand/available-time period.')
            result.update(takt=available/demand,unit=unit,series=[{'label':r.get('process','Process'),'value':number(r['cycle'])} for r in rows],formula='Takt = net available production time / customer demand, for the same period and time unit.')
        elif key=='yamazumi':
            need(rows,'operator','element','time');unit=uniform(rows,selected=meta.get('unit'));groups=defaultdict(float)
            for r in rows: groups[r['operator']]+=number(r['time'])
            takt=number(meta.get('takt'))
            if takt<=0: raise ValueError('Reference takt must be positive.')
            result.update(series=[{'label':k,'value':v} for k,v in groups.items()],unit=unit,takt=takt,formula='Sequential work element durations summed by operator; compare with stated takt. Overlap is not assumed.')
        elif key=='oee':
            need(rows,'planned','run','ideal_cycle','total','good','unit','period','source');series=[]
            for row in rows:
                planned,run,cycle,total,good=(number(row[f]) for f in ['planned','run','ideal_cycle','total','good'])
                if planned<=0 or run<=0 or total<=0 or cycle<=0: raise ValueError('OEE planned/run time, ideal cycle and total units must be positive.')
                if run>planned or good>total or cycle*total>run: raise ValueError('OEE requires run ≤ planned, good ≤ total and ideal cycle × total ≤ run; review units and definitions.')
                a=run/planned;p=cycle*total/run;q=good/total
                series.append({'label':row.get('asset','Asset'),'value':100*a*p*q,'availability':100*a,'performance':100*p,'quality':100*q})
            result.update(series=series,unit='%',formula='Availability = run/planned; performance = ideal cycle × total/run; quality = good/total; OEE = A × P × Q. Scheduled breaks excluded from planned production time.')
        elif key=='spaghetti':
            need(rows,'x','y','route','unit','state');uniform(rows);groups=defaultdict(list)
            for r in rows: groups[(r['route'],r['state'])].append(r)
            result.update(routes=[{'label':' / '.join(k),'points':v,'distance':sum(math.hypot(number(b['x'])-number(a['x']),number(b['y'])-number(a['y'])) for a,b in zip(v,v[1:]))} for k,v in groups.items()],formula='Euclidean segment distances in measured coordinates, summed separately by route and current/future state; no obstacle routing.')
        elif key=='vsm':
            need(rows,'step','state','cycle','wait','unit');unit=uniform(rows);totals=defaultdict(lambda:{'cycle':0,'wait':0})
            for r in rows:
                totals[r['state']]['cycle']+=number(r['cycle']);totals[r['state']]['wait']+=number(r['wait'])
            result.update(totals=dict(totals),unit=unit,formula='Sum recorded cycle and waiting times separately per state, same unit; parallel paths are not automatically summed as lead time.')
        elif key=='kanban':
            need(rows,'lane','wip','limit');result['series']=[{'label':r['lane'],'value':number(r['wip']),'limit':number(r['limit'])} for r in rows]
            result['formula']='Observed WIP compared with the explicitly local limit; no automatic release instruction.'
        elif key=='smed':
            need(rows,'element','before','after','unit');uniform(rows)
            result['series']=[{'label':r['element'],'value':number(r['before']),'after':number(r['after'])} for r in rows]
            result['formula']='Observed current versus proposed duration by element; proposed time is not validated savings.'
        elif key=='5s':
            rated=[number(r['score']) for r in rows if r.get('score') not in ('',None)]
            result.update(local_score=sum(rated) if rated else None,rated_count=len(rated),formula='Local 0 absent / 1 partly demonstrated / 2 demonstrated. Sum only rated observations; no official TCA relationship.')
    except (ValueError,TypeError,KeyError,OverflowError) as error:
        result['messages'].append(str(error));result['incomplete']=True
    return result
