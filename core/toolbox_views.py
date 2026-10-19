"""Additive toolbox and report routes using the existing site access boundary."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Kaizen, Worksheet, WorksheetRevision, Evidence
from .views import site_access, log
from .kaizen import checkpoint, reopen_after_change

EDIT_ROLES=['staff','coach','manager','admin']

def worksheet_checkpoint(worksheet,user):
    WorksheetRevision.objects.get_or_create(worksheet=worksheet,revision=worksheet.revision,
        defaults={'schema_version':worksheet.schema_version,'payload':worksheet.payload,'actor':user})

def validate_links(event,user,payload):
    from .access import allowed_classifications
    links=payload.get('links',{})
    sources={'actions':event.actions.all(),'observations':event.observations.all(),
             'evidence':Evidence.objects.filter(site=event.site,classification__in=allowed_classifications(user,event.site))}
    for name,source in sources.items():
        values=links.get(name,[])
        if not isinstance(values,list): raise ValueError('Links must be lists of IDs.')
        try: selected={int(v) for v in values}
        except (ValueError,TypeError): raise ValueError('Linked IDs must be integers.')
        if not selected.issubset(set(source.values_list('pk',flat=True))): raise ValueError('A linked object is unavailable in this event/site.')
    for row in payload.get('rows',[]):
        if row.get('evidence_id'):
            try: key=int(row['evidence_id'])
            except (ValueError,TypeError): raise ValueError('Evidence ID must be an integer.')
            if not sources['evidence'].filter(pk=key).exists(): raise ValueError('Cause evidence must be authorized evidence from this site.')
        for field in ('before_attachment','after_attachment'):
            if row.get(field):
                from .access import visible_attachments
                if not str(row[field]).isdigit() or not visible_attachments(event,user).filter(pk=row[field]).exists(): raise ValueError('Photo references must be authorized event attachments.')
        if row.get('worksheet_id') and (not str(row['worksheet_id']).isdigit() or not event.worksheets.filter(pk=row['worksheet_id']).exists()): raise ValueError('Guidance must reference a worksheet in this event.')

@login_required
def toolbox(request,site_code,pk):
    from .toolbox_registry import REGISTRY,initial_payload
    site=site_access(request,site_code);event=get_object_or_404(Kaizen,pk=pk,site=site)
    if request.method=='POST':
        site_access(request,site_code,EDIT_ROLES)
        key=request.POST.get('method');stage=request.POST.get('stage','Plan')
        if key not in REGISTRY or stage not in ('Plan','Do','Check','Act'): return JsonResponse({'error':'Choose a registered method and PDCA stage.'},status=422)
        with transaction.atomic():
            event=Kaizen.objects.select_for_update().get(pk=event.pk)
            if str(event.revision)!=request.POST.get('revision'): return JsonResponse({'error':'Another event edit was saved. Reload.'},status=409)
            checkpoint(event,request.user,'Before adding worksheet')
            w=Worksheet.objects.create(event=event,method=key,stage=stage,title=REGISTRY[key]['name'],payload=initial_payload(key,event))
            worksheet_checkpoint(w,request.user);reopen_after_change(event);event.revision+=1;event.save();checkpoint(event,request.user,'Added '+w.title)
        return redirect('worksheet',site_code=site.code,pk=pk,worksheet_pk=w.pk)
    stage=request.GET.get('stage','Plan');q=request.GET.get('q','').casefold()
    specs=[s for s in REGISTRY.values() if q in (s['name']+' '+s['purpose']).casefold() and all(not request.GET.get(f) or s[f]==request.GET[f] for f in ('goal','stage','data_need','difficulty'))]
    suggestions={'Plan':[('5w2h','Clarify the problem without repeating saved context.'),('ishikawa','Explore an unknown cause as hypotheses.'),('5whys','Trace a recurring gap and check evidence.')],
                 'Do':[('impact-effort','Compare practical changes.'),('fmea','Review failure risks before changing work.'),('5s','Make a workplace standard visible.')],
                 'Check':[('pareto','Prioritize measured categories.'),('run-chart','Inspect a measure over time.'),('takt','Compare cycle times with period demand.')],
                 'Act':[('control-plan','Assign sustain checks and reaction.'),('standard-work','Retain the proven work sequence.'),('kata','Plan the next evidence-based experiment.')]}.get(stage,[])
    return render(request,'toolbox.html',{'site':site,'event':event,'stage':stage,'specs':specs,'suggestions':[(REGISTRY[k],reason) for k,reason in suggestions],
        'filters':[(name,sorted({s[name] for s in REGISTRY.values()}),request.GET.get(name,'')) for name in ('goal','stage','data_need','difficulty')],
        'query':request.GET.get('q',''),'can_edit':bool(site.membership_set.filter(user=request.user,role__in=EDIT_ROLES))})

@login_required
def worksheet(request,site_code,pk,worksheet_pk):
    import json
    from copy import deepcopy
    from .toolbox_registry import REGISTRY,migrate_payload
    from .toolbox_math import validate_payload,calculate
    from .toolbox_visuals import render_svg
    from .access import allowed_classifications
    site=site_access(request,site_code);event=get_object_or_404(Kaizen,site=site,pk=pk)
    w=get_object_or_404(Worksheet,event=event,pk=worksheet_pk)
    if w.method not in REGISTRY: raise Http404
    if request.method=='POST':
        site_access(request,site_code,EDIT_ROLES)
        try:
            if len(request.body)>2*1024*1024: raise ValueError('Worksheet request exceeds 2 MB; split large datasets into worksheets.')
            posted=json.loads(request.body) if request.content_type=='application/json' else request.POST.dict()
            with transaction.atomic():
                event=Kaizen.objects.select_for_update().get(pk=pk);w=Worksheet.objects.select_for_update().get(pk=worksheet_pk,event=event)
                if str(event.revision)!=str(posted.get('event_revision')) or str(w.revision)!=str(posted.get('revision')):
                    return JsonResponse({'error':'Another edit was saved. Entries remain here; review the latest version before retrying.'},status=409)
                if w.schema_version!=REGISTRY[w.method]['version']:
                    return JsonResponse({'error':'This worksheet uses an older schema. Migrate it explicitly before editing.'},status=409)
                payload=posted.get('payload')
                if posted.get('restore') is not None:
                    prior=get_object_or_404(WorksheetRevision,worksheet=w,revision=posted['restore']);payload=migrate_payload(w.method,prior.payload,prior.schema_version,REGISTRY[w.method]['version'])
                if not isinstance(payload,dict): raise ValueError('Supply a structured worksheet.')
                payload=deepcopy(payload)
                # Omitted row IDs are archived, never silently dropped from the record.
                ids={r.get('id') for r in payload.get('rows',[]) if isinstance(r,dict)}
                for row in w.payload.get('rows',[]):
                    if row['id'] not in ids: payload.setdefault('rows',[]).append({**row,'archived':True})
                validate_payload(w.method,payload);validate_links(event,request.user,payload)
                checkpoint(event,request.user,'Before worksheet change');worksheet_checkpoint(w,request.user)
                w.payload=payload;w.schema_version=REGISTRY[w.method]['version'];w.revision+=1
                w.include_in_a3=bool(payload.get('include_in_a3',True));w.save();worksheet_checkpoint(w,request.user)
                reopen_after_change(event);event.revision+=1;event.save();checkpoint(event,request.user,'Worksheet '+w.title+' saved')
                log(site,request.user,'worksheet_saved',w,{'revision':w.revision})
            return JsonResponse({'revision':w.revision,'event_revision':event.revision,'payload':payload,'analysis':calculate(w.method,payload),'svg':render_svg(w.method,payload)})
        except (ValueError,TypeError,json.JSONDecodeError) as error: return JsonResponse({'error':str(error)},status=422)
    can_edit=site.membership_set.filter(user=request.user,role__in=EDIT_ROLES).exists()
    return render(request,'worksheet.html',{'site':site,'event':event,'worksheet':w,'spec':REGISTRY[w.method],
        'payload':w.payload,'analysis':calculate(w.method,w.payload),'svg':render_svg(w.method,w.payload),
        'can_edit':can_edit,'worksheet_history':w.history.all()[:20],
        'link_options':{'actions':list(event.actions.values('id','description')),'observations':list(event.observations.values('id','measure','value','unit')),
                        'evidence':list(Evidence.objects.filter(site=site,classification__in=allowed_classifications(request.user,site)).values('id','title'))}})

@login_required
def worksheet_export(request,site_code,pk,worksheet_pk,fmt):
    import json,csv
    from io import StringIO
    from .toolbox_registry import REGISTRY
    from .toolbox_visuals import render_svg
    site=site_access(request,site_code);event=get_object_or_404(Kaizen,site=site,pk=pk);w=get_object_or_404(Worksheet,event=event,pk=worksheet_pk)
    if fmt=='json': return JsonResponse({'method':w.method,'schema_version':w.schema_version,'revision':w.revision,'payload':w.payload,'history':list(w.history.values())},json_dumps_params={'indent':2})
    if fmt=='svg': response=HttpResponse(render_svg(w.method,w.payload),content_type='image/svg+xml')
    elif fmt=='csv':
        output=StringIO();writer=csv.writer(output);headers=['id','archived']+[f['key'] for f in REGISTRY[w.method]['fields']]
        safe=lambda v:"'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v
        writer.writerow(['Metadata',json.dumps(w.payload.get('meta',{})), 'Conclusion',safe(w.payload.get('conclusion',''))]);writer.writerow(headers)
        for row in w.payload['rows']: writer.writerow([safe(row.get(k,'')) for k in headers])
        response=HttpResponse(output.getvalue(),content_type='text/csv; charset=utf-8')
    else: raise Http404
    response['Content-Disposition']=f'attachment; filename="worksheet-{w.pk}-r{w.revision}.{fmt}"'
    return response

@login_required
@require_POST
def input_profile(request,site_code,pk):
    from .profiles import PROFILES
    site=site_access(request,site_code,EDIT_ROLES)
    selected=request.POST.get('input_profile')
    if selected not in PROFILES: return JsonResponse({'error':'Choose a valid input profile.'},status=422)
    with transaction.atomic():
        event=get_object_or_404(Kaizen.objects.select_for_update(),pk=pk,site=site)
        if str(event.revision)!=request.POST.get('revision'): return JsonResponse({'error':'Another edit was saved. Reload before switching.'},status=409)
        checkpoint(event,request.user,'Before input profile switch')
        event.input_profile=selected;event.revision+=1;event.save()
        checkpoint(event,request.user,'Input profile switched; full detail retained')
        log(site,request.user,'input_profile_switched',event,{'input_profile':selected})
    messages.success(request,'Input view changed. All saved detail and methodological classification retained.')
    return redirect('kaizen_detail',site_code=site.code,pk=pk)
