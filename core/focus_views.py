"""Attach evidence to a question without leaving the assessment (focus view side panel)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from .access import allowed_classifications
from .models import Assessment, Coverage, Evidence, Requirement
from .progress import scope_for
from .views import log, site_access

ALLOWED = ('pdf', 'png', 'jpg', 'jpeg', 'xlsx', 'docx', 'txt')


@login_required
@require_POST
def attach_evidence(request, site_code, req_code):
    site = site_access(request, site_code, ['assessor', 'manager', 'admin'])
    assessment = get_object_or_404(Assessment, site=site, pk=request.POST.get('assessment_id') or 0)
    req = get_object_or_404(Requirement, code=req_code)
    if req.code not in scope_for(assessment).get('requirements', []): return redirect('assessment', site_code=site.code)
    back = request.POST.get('next', '')
    if not back.startswith(f'/sites/{site.code}/assessment/'): back = f'/sites/{site.code}/assessment/?assessment={assessment.pk}'
    clauses = list(req.clauses.order_by('ordinal'))
    chosen = {int(v) for v in request.POST.getlist('parts') if v.isdigit()}
    parts = [c for c in clauses if c.ordinal in chosen] or clauses
    existing_id = request.POST.get('existing', '')
    upload = request.FILES.get('file')
    accept = request.POST.get('accept') == 'on'
    reason = request.POST.get('reason', '').strip()
    problem = ''
    if bool(upload) == bool(existing_id): problem = 'Choose one file to upload, or one document that is already in the evidence library.'
    elif upload and (upload.name.rsplit('.', 1)[-1].lower() not in ALLOWED): problem = f'{upload.name} is not an accepted file type. Use PDF, Excel, Word, an image or a text file.'
    elif upload and upload.size > 10 * 1024 * 1024: problem = f'{upload.name} is larger than 10 MB. Reduce the file or share a smaller extract.'
    elif upload and upload.name.rsplit('.', 1)[-1].lower() in ('pdf', 'png', 'jpg', 'jpeg', 'xlsx'):
        from django import forms
        from .files import checked_upload
        try: checked_upload(upload)
        except forms.ValidationError as error: problem = f'{upload.name}: {error.messages[0]} Nothing was attached.'
    if not problem and accept and not reason: problem = 'Write why the evidence is acceptable before accepting it, so the decision can be audited later. You can also attach it now and accept it later.'
    if problem:
        messages.error(request, problem); return redirect(back)
    with transaction.atomic():
        if upload:
            item = Evidence.objects.create(site=site, title=request.POST.get('title', '').strip()[:255] or upload.name[:255],
                evidence_type=request.POST.get('evidence_type') if request.POST.get('evidence_type') in ('document', 'observation', 'interview') else 'document',
                owner=request.user.get_full_name() or request.user.username, source=f'Attached during assessment v{assessment.version}, {req.label}',
                file=upload, created_by=request.user)
            log(site, request.user, 'evidence_created', item, {'requirement': req.code, 'from': 'focus'})
        else:
            item = get_object_or_404(Evidence, site=site, pk=existing_id if existing_id.isdigit() else 0,
                                     classification__in=allowed_classifications(request.user, site))
        if accept and item.valid_until and item.valid_until < timezone.localdate():
            transaction.set_rollback(True)
            messages.error(request, f'"{item.title}" expired on {item.valid_until:%d %b %Y}. Expired evidence cannot be accepted; attach a current version.')
            return redirect(back)
        if accept and item.evidence_type == 'audit':
            accept = False  # another audit needs its scope recorded first (evidence library)
        for clause in parts:
            link, _ = Coverage.objects.get_or_create(evidence=item, clause=clause)
            if accept:
                link.accepted = True; link.decision = reason; link.reviewed_by = request.user; link.reviewed_at = timezone.now(); link.save()
                log(site, request.user, 'coverage_reviewed', link, {'accepted': True, 'from': 'focus'})
    count = len(parts)
    messages.success(request, f'"{item.title}" linked to {req.label} ({count} part{"s" if count != 1 else ""})'
                              + (' and accepted.' if accept else '. It counts once an assessor accepts it.'))
    return redirect(back)
