from pathlib import Path
from uuid import uuid4
from datetime import date
from decimal import Decimal
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import FileResponse,Http404,JsonResponse
from django.shortcuts import get_object_or_404,redirect,render
from .models import *
from .views import site_access,log
from .access import allowed_classifications,visible_attachments
from .files import checked_upload,read_table
from .kaizen import checkpoint,reopen_after_change,reuse_observations
from .forms import ObservationForm
from .toolbox_registry import REGISTRY,initial_payload
from .toolbox_math import validate_payload
from .toolbox_views import EDIT_ROLES,worksheet_checkpoint,validate_links

class AttachmentForm(forms.Form):
    stage=forms.ChoiceField(choices=[(s,s) for s in ('Plan','Do','Check','Act')])
    title=forms.CharField(max_length=200)
    file=forms.FileField(required=False,label='Upload file (does not import data)')
    evidence=forms.ModelChoiceField(queryset=Evidence.objects.none(),required=False,label='Or link existing site evidence')
    requirement=forms.ModelChoiceField(queryset=Requirement.objects.all(),required=False)
    version=forms.CharField(max_length=80,initial='1')
    provenance=forms.CharField(widget=forms.Textarea(attrs={'rows':2}),label='Origin / measurement context')
    classification=forms.ChoiceField(choices=[('internal','Internal'),('financial','Financial restricted'),('hr','HR restricted')])
    revision=forms.IntegerField(widget=forms.HiddenInput)
    def clean(self):
        data=super().clean()
        if bool(data.get('file'))==bool(data.get('evidence')): raise forms.ValidationError('Upload one file or link one existing evidence record.')
        if data.get('file'):
            data['file'],data['sha256']=checked_upload(data['file'])
        return data

def attachment_form(request,event,stage):
    allowed=allowed_classifications(request.user,event.site)
    form=AttachmentForm(request.POST or None,request.FILES or None,initial={'stage':stage,'revision':event.revision,'classification':'internal'},auto_id='attachment_%s')
    form.fields['evidence'].queryset=Evidence.objects.filter(site=event.site,classification__in=allowed)
    form.fields['classification'].choices=[c for c in form.fields['classification'].choices if c[0] in allowed]
    return form

@login_required
def attachment_add(request,site_code,pk):
    site=site_access(request,site_code,EDIT_ROLES);event=get_object_or_404(Kaizen,pk=pk,site=site)
    form=attachment_form(request,event,request.GET.get('stage','Check'))
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            event=Kaizen.objects.select_for_update().get(pk=pk)
            if event.revision!=form.cleaned_data['revision']: form.add_error(None,'Another event edit was saved. Your entries remain here; reload the latest revision before retrying.')
            else:
                checkpoint(event,request.user,'Before adding attachment');d=form.cleaned_data;linked=d.get('evidence')
                attachment=EventAttachment(event=event,stage=d['stage'],title=d['title'],evidence=linked,requirement=d['requirement'],version=d['version'],provenance=d['provenance'],
                    classification=linked.classification if linked else d['classification'],created_by=request.user)
                if d.get('file'):
                    attachment.original_name=Path(d['file'].name).name;attachment.sha256=d['sha256'];attachment.file=d['file']
                attachment.save();reopen_after_change(event);event.revision+=1;event.save();checkpoint(event,request.user,'Attachment added (bytes unchanged)')
                log(site,request.user,'event_attachment_added',attachment,{'sha256':attachment.sha256})
                return redirect('kaizen_detail',site_code=site.code,pk=pk)
    return render(request,'attachment_form.html',{'site':site,'event':event,'form':form})

@login_required
def attachment_download(request,site_code,pk,attachment_pk):
    site=site_access(request,site_code);event=get_object_or_404(Kaizen,pk=pk,site=site)
    item=get_object_or_404(visible_attachments(event,request.user),pk=attachment_pk)
    if item.evidence:
        if item.evidence.site_id!=site.pk or item.evidence.classification not in allowed_classifications(request.user,site): raise Http404
        return redirect('download',site_code=site.code,pk=item.evidence_id)
    if not item.file: raise Http404
    response=FileResponse(item.file.open('rb'),as_attachment=True,filename=item.original_name)
    response['Cache-Control']='private, no-store';return response

@login_required
def attachment_preview(request,site_code,pk,attachment_pk):
    import mimetypes
    site=site_access(request,site_code);event=get_object_or_404(Kaizen,pk=pk,site=site)
    item=get_object_or_404(visible_attachments(event,request.user),pk=attachment_pk)
    file=item.file
    name=item.original_name
    if item.evidence:
        if item.evidence.site_id!=site.pk or item.evidence.classification not in allowed_classifications(request.user,site):raise Http404
        file=item.evidence.file;name=file.name if file else ''
    if not file or Path(name).suffix.lower() not in ('.png','.jpg','.jpeg'):raise Http404
    response=FileResponse(file.open('rb'),content_type=mimetypes.guess_type(name)[0],as_attachment=False)
    response['Cache-Control']='private, no-store';return response

@login_required
def import_preview(request,site_code,pk):
    site=site_access(request,site_code,EDIT_ROLES);event=get_object_or_404(Kaizen,pk=pk,site=site)
    form=forms.Form(request.POST or None)
    form.fields['attachment']=forms.ModelChoiceField(queryset=visible_attachments(event,request.user).exclude(file=''),label='Original event CSV / XLSX')
    form.fields['sheet']=forms.CharField(required=False,label='XLSX worksheet (blank selects the first)')
    if request.method=='POST' and form.is_valid():
        try:
            table=read_table(form.cleaned_data['attachment'],form.cleaned_data['sheet'])
            preview=ImportPreview.objects.create(event=event,attachment=form.cleaned_data['attachment'],table=table,created_by=request.user)
            return redirect('import_confirm',site_code=site.code,pk=pk,preview_pk=preview.pk)
        except Exception as error:
            # Parser errors from a user-supplied container must stay a form error.
            form.add_error(None,str(error) if isinstance(error,(ValueError,UnicodeError)) else 'Cannot read this table. Check that it is a valid CSV/XLSX with a header row and plain values. Original file retained.')
    return render(request,'import_preview.html',{'site':site,'event':event,'form':form})

@login_required
def import_confirm(request,site_code,pk,preview_pk):
    site=site_access(request,site_code,EDIT_ROLES);event=get_object_or_404(Kaizen,pk=pk,site=site)
    preview=get_object_or_404(ImportPreview,event=event,pk=preview_pk,attachment__classification__in=allowed_classifications(request.user,site))
    target=request.POST.get('target') or request.GET.get('target') or 'observations'
    if target!='observations' and target not in REGISTRY: target='observations'
    form=forms.Form(request.POST or None)
    names=['phase','measure','value','unit','population','period_start','period_end','data_source'] if target=='observations' else [f['key'] for f in REGISTRY[target]['fields']]
    choices=[('','Use constant below')]+[(str(i),f'{i+1}: {name}') for i,name in enumerate(preview.table['headers'])]
    for name in names:
        form.fields['column_'+name]=forms.ChoiceField(choices=choices,required=False,label=name.replace('_',' ').capitalize()+' source column')
        form.fields['constant_'+name]=forms.CharField(required=False,label=name.replace('_',' ').capitalize()+' constant')
    form.fields['revision']=forms.IntegerField(widget=forms.HiddenInput,initial=event.revision)
    for f in (REGISTRY[target]['meta'] if target in REGISTRY else []):
        form.fields['meta_'+f['key']]=forms.CharField(required=False,label=f['label']+' (worksheet setting)')
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            event=Kaizen.objects.select_for_update().get(pk=pk);preview=ImportPreview.objects.select_for_update().get(pk=preview_pk)
            if event.revision!=form.cleaned_data['revision'] or preview.confirmed: form.add_error(None,'The event changed or import was already confirmed. Original preview and file retained; reload and review before importing.')
            else:
                mapped=[]
                for index,row in enumerate(preview.table['rows'],2):
                    values={name:row[int(form.cleaned_data['column_'+name])] if form.cleaned_data['column_'+name] else form.cleaned_data['constant_'+name] for name in names}
                    if target=='observations':
                        row_form=ObservationForm(values)
                        if not row_form.is_valid(): form.add_error(None,f'Source row {index}: '+str(row_form.errors.as_text()))
                        else: mapped.append(row_form)
                    else: mapped.append({'id':str(uuid4()),'archived':False,**values})
                payload=None
                if target in REGISTRY:
                    payload=initial_payload(target,event);payload['rows']=mapped;payload['meta'].update({f['key']:form.cleaned_data['meta_'+f['key']] for f in REGISTRY[target]['meta']});payload['import_origin']={'attachment':preview.attachment_id,'sha256':preview.attachment.sha256,'sheet':preview.table['sheet']}
                    try: validate_payload(target,payload);validate_links(event,request.user,payload)
                    except ValueError as error: form.add_error(None,str(error))
                if not mapped: form.add_error(None,'No valid source rows. Nothing imported.')
                if not form.errors:
                    checkpoint(event,request.user,'Before confirmed measurement import')
                    if target=='observations':
                        for row_form in mapped: obj=row_form.save(commit=False);obj.event=event;obj.save()
                        reuse_observations(event)
                    else:
                        worksheet=Worksheet.objects.create(event=event,method=target,stage='Check',title=REGISTRY[target]['name']+' (imported)',payload=payload);worksheet_checkpoint(worksheet,request.user)
                    preview.mapping={'target':target,'fields':form.cleaned_data};preview.confirmed=True;preview.save();reopen_after_change(event);event.revision+=1;event.save();checkpoint(event,request.user,'Confirmed import; original file retained')
                    log(site,request.user,'measurement_import_confirmed',preview,{'rows':len(mapped),'target':target})
                    messages.success(request,f'{len(mapped)} rows imported after confirmed mapping. Original bytes retained.')
                    return redirect('kaizen_detail',site_code=site.code,pk=pk)
    return render(request,'import_confirm.html',{'site':site,'event':event,'preview':preview,'form':form,'target':target,
        'targets':[('observations','Event before/after observations')]+[(k,s['name']) for k,s in REGISTRY.items()],
        'rows':preview.table['rows'][:10],'headers':preview.table['headers'],'row_count':len(preview.table['rows'])})
