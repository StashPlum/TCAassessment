"""Administration of the catalogue in use and of each site's TCA group (with a preview before saving)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from .catalogue import active_catalogue, group_preview, site_group
from .context import authorized_sites
from .models import AuditEvent, Membership, Site, TCAGroup


def _admin_site(request, site_code):
    site = get_object_or_404(Site, code=site_code)
    if not Membership.objects.filter(user=request.user, site=site, role='admin').exists(): raise Http404
    return site


@login_required
def administration(request):
    sites = list(authorized_sites(request.user).filter(membership__user=request.user, membership__role='admin').distinct())
    if not sites: raise Http404
    catalogue = active_catalogue()
    for site in sites: site.mapped_group = site_group(site, catalogue)
    return render(request, 'administration.html', {'sites': sites, 'catalogue': catalogue,
        'unmapped': sum(1 for s in sites if catalogue and not s.mapped_group)})


@login_required
def site_group_map(request, site_code):
    site = _admin_site(request, site_code)
    catalogue = active_catalogue()
    if catalogue is None:
        messages.info(request, 'No group-specific catalogue is active. Sites use the global catalogue.')
        return redirect('administration')
    groups = list(catalogue.groups.all())
    current = site_group(site, catalogue)
    chosen = request.POST.get('group') if request.method == 'POST' else request.GET.get('group', '')
    group = next((g for g in groups if g.code == chosen), None)
    if chosen and group is None: raise Http404
    preview = group_preview(catalogue, group) if group else None
    if request.method == 'POST':
        if group is None or not preview['valid']:
            messages.error(request, 'Choose a group whose preview shows 150 questions before saving.')
        elif request.POST.get('confirm') != 'yes':
            messages.error(request, 'Tick the confirmation to save this mapping. It decides which wording the next assessment uses.')
        else:
            with transaction.atomic():
                locked = Site.objects.select_for_update().get(pk=site.pk)
                before = locked.tca_group.code if locked.tca_group else None
                locked.tca_group = group; locked.save(update_fields=['tca_group'])
                AuditEvent.objects.create(site=site, actor=request.user, action='tca_group_mapped', object_type='Site', object_id=str(site.pk),
                                          detail={'catalogue': catalogue.key, 'before': before, 'after': group.code})
            messages.success(request, f'{site.name} now uses {group.code}. The next new assessment uses this group; open or approved assessments keep their own questions.')
            return redirect('administration')
    return render(request, 'site_group_map.html', {'site': site, 'catalogue': catalogue, 'groups': groups, 'current': current,
        'group': group, 'preview': preview, 'has_draft': site.assessments.filter(status='draft').exists()})
