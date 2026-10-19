"""Complete operational archive export; no claims of source workbook formula parity."""
from io import BytesIO
from openpyxl import Workbook

EXTERNAL_TEXT_LIMITS={
    'title': ('TEAM!G10',75),
    'measure': ('PLAN!G24:M24',200),
}

def export_errors(event):
    problems=[]
    for key,(source,limit) in EXTERNAL_TEXT_LIMITS.items():
        value=event.title if key=='title' else event.data.get(key,'')
        if len(str(value))>limit: problems.append(f'{key} has {len(str(value))} characters; source {source} permits {limit}.')
    for key,value in event.data.items():
        if len(str(value))>32767: problems.append(f'{key} exceeds the Excel cell limit of 32767 characters.')
    for relation in ('actions','observations','document_updates','participants','review_notes'):
        for record in getattr(event,relation).all():
            for field in record._meta.fields:
                value=getattr(record,field.name)
                if isinstance(value,str) and len(value)>32767:
                    problems.append(f'{relation} record {record.pk} {field.name} exceeds the Excel cell limit; use the complete JSON archive.')
    for worksheet in event.worksheets.all():
        for row in worksheet.payload.get('rows',[]):
            for key,value in row.items():
                if len(str(value))>32767: problems.append(f'Worksheet {worksheet.pk} row {row.get("id")} {key} exceeds the Excel cell limit; use JSON/ZIP.')
        for key,value in worksheet.payload.get('meta',{}).items():
            if len(str(value))>32767: problems.append(f'Worksheet {worksheet.pk} {key} exceeds the Excel cell limit; use JSON/ZIP.')
        if len(worksheet.payload.get('conclusion',''))>32767: problems.append(f'Worksheet {worksheet.pk} conclusion exceeds the Excel cell limit; use JSON/ZIP.')
    return problems

def archive_xlsx(event, include_financial, include_participants, user=None):
    wb=Workbook()
    fields=wb.active;fields.title='PDCA Fields';fields.append(['Field','Value','Source / note'])
    fields.append(['title',event.title,'TEAM!G10'])
    fields.append(['profile',event.profile,'COACH REVIEW!C12'])
    fields.append(['status',event.status,'TCA Progress workflow'])
    mapping={'overall_problem':'PLAN!B11','specific_problem':'PLAN!B63','root_cause':'PLAN!B85',
             'measure':'PLAN!B24','baseline':'PLAN!B27','target':'PLAN!B30','solution':'DO!B15',
             'actual':'CHECK!B26','sustain':'ACT!D1','document_types':'ACT!H9:K40',
             'coach_review':'COACH REVIEW!B10:F77'}
    for key,value in event.data.items(): fields.append([key,str(value),mapping.get(key,'Supplemental operational field')])
    fields.append(['input_profile',event.input_profile,'Application input view; not methodology'])
    fields.append(['local_status',event.local_status,'Local PDCA; not global submission'])
    actions=wb.create_sheet('Actions');actions.append(['Phase','Description','Owner','Start','End','Key action'])
    for a in event.actions.all(): actions.append([a.phase,a.description,a.owner,a.start_date,a.end_date,a.key_action])
    participants=wb.create_sheet('Participants');participants.append(['Initial','Last name','Email','Role profile','Kaizen role','Estimated hours'])
    if include_participants:
        for p in event.participants.all(): participants.append([p.first_initial,p.last_name,p.email,p.role_profile,p.kaizen_role,float(p.estimated_hours) if p.estimated_hours is not None else None])
    documents=wb.create_sheet('Document updates');documents.append(['Type','Number','Name','Date updated'])
    for d in event.document_updates.all(): documents.append([d.document_type,d.document_number,d.name,d.updated_at])
    observations=wb.create_sheet('Observations');observations.append(['Phase','Measure','Value','Unit','Population','Period start','Period end','Data source'])
    for o in event.observations.all(): observations.append([o.phase,o.measure,float(o.value),o.unit,o.population,o.period_start,o.period_end,o.data_source])
    benefits=wb.create_sheet('Benefits');benefits.append(['Type','Amount','Unit','Period start','Period end','Validated'])
    if include_financial:
        for b in event.benefits.all(): benefits.append([b.kind,float(b.amount),b.unit,b.period_start,b.period_end,b.validated])
    linked=wb.create_sheet('Linked TCA');linked.append(['Requirement ID','Official detail','Source'])
    for r in event.linked_requirements.all(): linked.append([r.code,r.detail_text,r.source_address])
    notes=wb.create_sheet('Compatibility');notes.append(['Check','Result'])
    notes.append(['Original template formulas','Not recalculated or imported'])
    notes.append(['AUTO_UPLOAD','Legacy selector mapping only; no corporate API verified'])
    notes.append(['Source limits','Checked for known mapped fields; see docs/SOURCE_MAP.md'])
    reviews=wb.create_sheet('Review advice');reviews.append(['Stage','Type','Advice','Actor ID','Revision','Resolved','Date'])
    for note in event.review_notes.all(): reviews.append([note.stage,note.kind,note.text,note.actor_id,note.event_revision,note.resolved,note.created_at.isoformat()])
    history=wb.create_sheet('Revision history');history.append(['Revision','State','Reason','Actor ID','Date','Full snapshot'])
    for row in event.history.all(): history.append([row.revision,row.state,row.reason,row.actor_id,row.created_at.isoformat(),'Full permission-filtered snapshot in JSON archive'])
    from .toolbox_registry import REGISTRY
    for worksheet in event.worksheets.all():
        sheet=wb.create_sheet(f'Tool {worksheet.pk}')
        sheet.append(['Method',worksheet.method,'Schema',worksheet.schema_version,'Revision',worksheet.revision])
        for key,value in worksheet.payload.get('meta',{}).items():sheet.append(['Setting',key,str(value)])
        sheet.append(['Conclusion',worksheet.payload.get('conclusion','')])
        names=['id','archived']+[f['key'] for f in REGISTRY.get(worksheet.method,{}).get('fields',[])]
        # Unknown extension fields are retained too.
        names+=sorted({k for r in worksheet.payload.get('rows',[]) for k in r}-set(names))
        sheet.append(names)
        for row in worksheet.payload.get('rows',[]):sheet.append([str(row.get(name,'')) for name in names])
    attachments=wb.create_sheet('Attachment provenance');attachments.append(['ID','Stage','Title','Original','SHA-256','Version','Origin','Evidence ID','Requirement'])
    from .access import visible_attachments
    for item in (visible_attachments(event,user) if user else event.attachments.none()):
        if item.classification=='internal' or include_financial:
            attachments.append([item.pk,item.stage,item.title,item.original_name,item.sha256,item.version,item.provenance,item.evidence_id,item.requirement_id])
    for sheet in wb:
        for row in sheet:
            for cell in row:
                if isinstance(cell.value,str): cell.data_type='s'  # user text is never an executable formula
        sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
        sheet.column_dimensions['A'].width=25;sheet.column_dimensions['B'].width=55;sheet.column_dimensions['C'].width=45
    output=BytesIO();wb.save(output);output.seek(0)
    return output
