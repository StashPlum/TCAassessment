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

SENSEI_ROLES={'coach','manager','admin'}

def site_roles(user,site):
    return set(Membership.objects.filter(user=user,site=site).values_list('role',flat=True))

def can_edit_event(user,event):
    """Coach/manager/admin edit any site event. Staff edit their own events and events whose
    user-linked team includes them; events without a linked team keep the earlier site-wide rule."""
    roles=site_roles(user,event.site)
    if roles&SENSEI_ROLES: return True
    if 'staff' not in roles: return False
    if event.created_by_id==user.pk: return True
    linked=event.participants.filter(user__isnull=False)
    return not linked.exists() or linked.filter(user=user).exists()

def can_manage_team(user,event):
    roles=site_roles(user,event.site)
    if roles&SENSEI_ROLES: return True
    if 'staff' not in roles: return False
    return event.created_by_id==user.pk or event.participants.filter(user=user,kaizen_role='Kaizen lead').exists()

def require_event_editor(user,event):
    from django.http import Http404
    if not can_edit_event(user,event): raise Http404('Only the event team can change this Kaizen.')
