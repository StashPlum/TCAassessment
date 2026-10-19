"""Shared private-object classification checks."""
from .models import Membership

def allowed_classifications(user,site):
    roles=set(Membership.objects.filter(user=user,site=site).values_list('role',flat=True))
    if not roles: return set()
    return {'internal'}|({'financial','hr'} if roles&{'manager','admin','assessor'} else set())

def visible_attachments(event,user):
    from django.db.models import Q
    allowed=allowed_classifications(user,event.site)
    return event.attachments.filter(classification__in=allowed).filter(Q(evidence__isnull=True)|Q(evidence__site=event.site,evidence__classification__in=allowed))

def report_visible(report,user):
    ids={a['id'] for a in report.snapshot.get('attachments',[])}
    return ids.issubset(set(visible_attachments(report.event,user).values_list('pk',flat=True)))
