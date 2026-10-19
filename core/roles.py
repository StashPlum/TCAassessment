"""Role labels and default information hierarchy; permissions remain site scoped."""
ROLE_LABELS={'assessor':'TCA auditor','manager':'Site manager','coach':'Sensei','staff':'Kaizen team member','admin':'Technical administrator'}
PRIORITY=('assessor','manager','coach','staff','admin')
RIGHTS={
    'assessor':('site_read','assessment_write','site_guidance_write','claim_review','restricted_read'),
    'manager':('site_read','assessment_write','local_snapshot_approve','claim_review','restricted_read','kaizen_write'),
    'coach':('site_read','kaizen_write','sensei_review'),
    'staff':('site_read','kaizen_write'),
    'admin':('site_read','technical_admin','assessment_write','local_snapshot_approve','claim_review','restricted_read','kaizen_write'),
}

def role_context(user,site):
    if not site: return {'primary_role':None,'role_label':'No site role','role_rights':set()}
    from .models import Membership
    roles=set(Membership.objects.filter(user=user,site=site).values_list('role',flat=True))
    primary=next((role for role in PRIORITY if role in roles),None)
    return {'primary_role':primary,'role_label':ROLE_LABELS.get(primary,'No site role'),
            'role_rights':set().union(*(RIGHTS.get(role,()) for role in roles))}
