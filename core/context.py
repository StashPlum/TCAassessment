"""Presentation context; location membership is always checked on the server."""
from .models import Membership, Site, SourceVersion
from django.urls import reverse
from .roles import role_context

AREAS = {
    'home': ('Overview','My work'), 'site': ('Overview','Site progress'),
    'locations': ('Overview','Authorized locations'),
    'preparation': ('Assessments','Prepare evidence'), 'sessions': ('Assessments','Plan assessment'),
    'preparation_need': ('Assessments','Documentation need'), 'session_detail': ('Assessments','Assessment plan'),
    'assessment_history': ('Assessments','Assessment history'),
    'assessment': ('Assessments','Conduct assessment'), 'respond': ('Assessments','Requirement response'),
    'opportunities': ('Improvements','TCA matrix'), 'kaizens': ('Improvements','Kaizen events'),
    'kaizen_detail': ('Improvements','PDCA workspace'), 'kaizen_template_details': ('Improvements','Supporting template fields'),
    'review_queue': ('Improvements','Sensei review'), 'kaizen_review_detail': ('Improvements','Sensei review'),
    'toolbox_library': ('Improvements','Lean toolbox'),
    'input_profile': ('Improvements','Input profile'), 'toolbox': ('Improvements','Lean toolbox'),
    'worksheet': ('Improvements','Structured worksheet'), 'attachment_add': ('Improvements','Stage evidence'),
    'import_preview': ('Improvements','Measurement preview'), 'import_confirm': ('Improvements','Confirmed mapping'),
    'a3_preview': ('Improvements','A3 report'), 'learning': ('Improvements','Learning repository'),
    'learning_publish': ('Improvements','Sharing scope'), 'claims': ('Assessments','Requirement verification'),
    'claim_review': ('Assessments','Targeted requirement decision'),
    'assessment_configuration': ('Assessments','Site question guidance'), 'question_configuration': ('Assessments','Question version'),
    'evidence': ('Resources','Evidence library'), 'other_audit': ('Resources','Audit scope'),
    'resources': ('Resources','Reports and guidance'), 'administration': ('Administration','Access and configuration'),
}

def authorized_sites(user):
    return Site.objects.filter(membership__user=user).distinct().order_by('country_code','name')

def selected_site(request):
    sites=authorized_sites(request.user)
    code=(request.resolver_match.kwargs.get('site_code') if request.resolver_match else None) or request.session.get('selected_site')
    return sites.filter(code=code).first() or sites.first()

def workspace(request):
    from django.conf import settings
    demo={'demo_mode':getattr(settings,'DEMO',False)}
    if not request.user.is_authenticated: return demo
    sites=list(authorized_sites(request.user))
    site=selected_site(request)
    name=request.resolver_match.url_name if request.resolver_match else 'home'
    area,title=AREAS.get(name,('Resources','Workspace'))
    source=SourceVersion.objects.filter(filename='TCA assessment work categorisation.xlsx').first()
    parent={'Overview':'home','Assessments':'assessment','Improvements':'opportunities','Resources':'resources','Administration':'administration'}[area]
    area_url=reverse(parent,kwargs={'site_code':site.code}) if site and parent in ('assessment','opportunities','resources') else reverse('administration' if area=='Administration' else 'home')
    from .kaizen import initials
    from .demo_views import can_read_feedback
    demo['can_read_feedback']=demo['demo_mode'] and can_read_feedback(request.user)
    from .policy import navigation
    site_roles=set(Membership.objects.filter(user=request.user,site=site).values_list('role',flat=True)) if site else set()
    can_administer=Membership.objects.filter(user=request.user,role='admin').exists()
    return {**demo,'navigation':navigation(site_roles,site,name,can_administer),'user_initials':initials(request.user.get_full_name() or request.user.username),'workspace_site':site,'authorized_sites':sites,**role_context(request.user,site),
            'authorized_countries':[(code,dict(Site.COUNTRY_CHOICES).get(code,'Country not assigned')) for code in sorted({s.country_code for s in sites})],
            'workspace_assessment':site.assessments.first() if site else None,
            'baseline_reference':source.sha256[:8] if source else 'Not imported',
            'nav_area':area,'page_label':title,'current_route':name,'area_url':area_url,
            'site_switch_area':name if name in ('site','assessment','sessions','opportunities','kaizens','evidence','preparation','resources') else 'home',
            'can_administer':can_administer,
            'can_sensei':bool(site and Membership.objects.filter(user=request.user,site=site,role__in=['coach','manager','admin']).exists()),
            'can_configure':bool(site and Membership.objects.filter(user=request.user,site=site,role='assessor').exists())}
