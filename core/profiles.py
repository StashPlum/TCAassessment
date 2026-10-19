"""Application size profiles; source submission and quality gates stay separate."""
PROFILES = {
    'small': ('Small: quick PDCA', 'A bounded change with a directly testable outcome; one working page.'),
    'medium': ('Medium', 'A recurring issue needing cause investigation, measures and several actions.'),
    'extensive': ('Extensive', 'Several processes or teams; guided global-template detail.'),
}

def suggest_profile(cross_process=False, unknown_cause=False, recurring=False):
    if cross_process: return 'extensive', 'Several processes are involved; use the guided full detail.'
    if unknown_cause or recurring: return 'medium', 'Recurrence or an unknown cause calls for investigation and comparable measures.'
    return 'small', 'A bounded test can use compact PDCA. Safety, quality and customer review still apply.'

LOCAL_FIELDS = ('overall_problem','process_location','owner','outcome_criterion','solution','observed_result','result_date','sustain')

def local_checks(event):
    missing=[key.replace('_',' ').capitalize() for key in LOCAL_FIELDS if not str(event.data.get(key,'')).strip()]
    if not event.attachments.filter(stage='Check').exists(): missing.append('Check-stage result evidence')
    if event.review_notes.filter(kind__in=['return','clarify'],resolved=False).exists(): missing.append('Unresolved sensei requests')
    return missing

def route_checks(event):
    from .kaizen import review_checks
    return {'local':local_checks(event),'global':review_checks(event),
            'global_policy':'Missing User Guide: official global submission completeness is not certified.'}
