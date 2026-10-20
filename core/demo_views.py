"""Feedback for the hosted demo: any signed-in tester can leave a note; site managers read and export them."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .context import selected_site
from .library_views import _csv
from .models import DemoFeedback, Membership
from .roles import role_context

def can_read_feedback(user):
    return Membership.objects.filter(user=user,role__in=['manager','admin']).exists()

@login_required
@require_POST
def feedback_add(request):
    page=request.POST.get('page','/')
    if not url_has_allowed_host_and_scheme(page,allowed_hosts={request.get_host()},require_https=request.is_secure()) or not page.startswith('/'): page='/'
    text=request.POST.get('text','').strip()
    rating=request.POST.get('rating','')
    if rating not in ('good','unclear','problem'): rating=''
    if not text or len(text)>4000:
        messages.error(request,'Write your feedback (at most 4000 characters). Nothing was saved.');return redirect(page)
    site=selected_site(request)
    DemoFeedback.objects.create(user=request.user,site=site,page=page[:300],role=role_context(request.user,site)['role_label'],rating=rating,text=text)
    messages.success(request,'Thank you, your feedback is saved.')
    return redirect(page)

@login_required
def feedback_list(request):
    if not can_read_feedback(request.user): raise Http404
    items=DemoFeedback.objects.select_related('user','site')
    if request.GET.get('format')=='csv':
        return _csv('demo-feedback.csv',['Date','Tester','Role','Site','Page','Rating','Feedback'],
            [[f.created_at.strftime('%Y-%m-%d %H:%M'),f.user.get_full_name() or f.user.username,f.role,f.site.name if f.site else '',f.page,f.get_rating_display(),f.text] for f in items])
    return render(request,'feedback_list.html',{'items':items})
