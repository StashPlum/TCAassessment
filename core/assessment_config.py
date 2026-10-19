"""Frozen, append-only site guidance over the immutable global catalog."""
from django.utils import timezone
from .models import Requirement, SiteQuestionVersion


def _source_record(req):
    return {'version_id': None, 'question_text': req.detail_text,
            'evidence_items': [line.strip() for line in req.expected_evidence.splitlines() if line.strip()],
            'local_explanation': '', 'kind': 'global_source',
            'official_clauses': [{'ordinal': c.ordinal, 'address': c.source_address, 'text': c.exact_text} for c in req.clauses.all()],
            'source_address': req.source_address, 'source_hash': req.source_version.sha256}


def current_question(site, req):
    base=_source_record(req)
    version=SiteQuestionVersion.objects.filter(site=site,requirement=req,kind='local_guidance').first()
    if version:
        base.update({'version_id':version.pk,'question_text':version.question_text,
                     'evidence_items':version.evidence_items,'local_explanation':version.local_explanation,'kind':version.kind})
    return base


def frozen_configuration(site):
    reqs=Requirement.objects.select_related('source_version').prefetch_related('clauses')
    effective={}
    for version in SiteQuestionVersion.objects.filter(site=site,kind='local_guidance').order_by('requirement_id','-version'):
        effective.setdefault(version.requirement_id,version)
    items={}
    for req in reqs:
        item=_source_record(req)
        version=effective.get(req.code)
        if version:
            item.update({'version_id':version.pk,'question_text':version.question_text,
                         'evidence_items':version.evidence_items,'local_explanation':version.local_explanation,'kind':version.kind})
        items[req.code]=item
    return {'schema':'site-question-v1','site_id':site.pk,'frozen_at':timezone.now().isoformat(),'requirements':items}


def question_for_assessment(assessment,req):
    if assessment and assessment.configuration_snapshot:
        item=assessment.configuration_snapshot.get('requirements',{}).get(req.code)
        if item: return item
    # Legacy assessments have no local configuration: their global source wording is retained.
    return _source_record(req)
