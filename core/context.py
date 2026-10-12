"""Presentation context; location membership is always checked on the server."""
from .models import Membership, Site, SourceVersion
from django.urls import reverse

AREAS = {
    'home': ('Overview','My work'), 'site': ('Overview','Site progress'),
    'locations': ('Overview','Authorized locations'),
    'preparation': ('Assessments','Prepare evidence'), 'sessions': ('Assessments','Plan assessment'),
    'assessment': ('Assessments','Conduct assessment'), 'respond': ('Assessments','Requirement response'),
    'opportunities': ('Improvements','Actions and blockers'), 'kaizens': ('Improvements','Kaizen events'),
    'kaizen_detail': ('Improvements','PDCA workspace'), 'kaizen_template_details': ('Improvements','Supporting template fields'),
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
    if not request.user.is_authenticated: return {}
    sites=list(authorized_sites(request.user))
    site=selected_site(request)
    name=request.resolver_match.url_name if request.resolver_match else 'home'
    area,title=AREAS.get(name,('Resources','Workspace'))
    source=SourceVersion.objects.filter(filename='TCA assessment work categorisation.xlsx').first()
    parent={'Overview':'home','Assessments':'assessment','Improvements':'kaizens','Resources':'resources','Administration':'administration'}[area]
    area_url=reverse(parent,kwargs={'site_code':site.code}) if site and parent in ('assessment','kaizens','resources') else reverse('administration' if area=='Administration' else 'home')
    return {'workspace_site':site,'authorized_sites':sites,
            'authorized_countries':[(code,dict(Site.COUNTRY_CHOICES).get(code,'Country not assigned')) for code in sorted({s.country_code for s in sites})],
            'workspace_assessment':site.assessments.first() if site else None,
            'baseline_reference':source.sha256[:8] if source else 'Not imported',
            'nav_area':area,'page_label':title,'current_route':name,'area_url':area_url,
            'site_switch_area':name if name in ('site','assessment','sessions','opportunities','kaizens','evidence','preparation','resources') else 'home',
            'can_administer':Membership.objects.filter(user=request.user,role='admin').exists()}
