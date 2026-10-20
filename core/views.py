from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import ActionForm, BenefitForm, DocumentUpdateForm, EvidenceForm, KaizenForm, KaizenStageForm, KaizenTemplateForm, ObservationForm, OpportunityForm, OtherAuditForm, ParticipantForm, PreparationFilterForm, ResponseForm, ReviewNoteForm, ReviewQueueForm, SessionForm, TeamMemberForm
from .models import Assessment, AssessmentSession, AuditEvent, Benefit, Category, Clause, Coverage, Evidence, Kaizen, KaizenAction, Membership, Opportunity, OtherAudit, Participant, Requirement, Response, ReviewNote, Site
from .scoring import category_result
from .measurements import compare_observations, event_benefits
from .quality import results_criterion, sustain_types_criterion
from .exports import archive_xlsx, export_errors
from .readiness import accepted_codes, assessment_snapshot
from .context import authorized_sites, selected_site
from .kaizen import initials, REVIEW_KEYS, REVIEW_STATE_LABELS, changed_since_review, checkpoint, current_phase, document_type_count, gantt, gate_summary, measurement_warnings, pdca_segments, public_snapshot, reopen_after_change, review_checks, review_state, reuse_observations, snapshot, team_display
from .access import can_edit_event, can_manage_team, require_event_editor
from .profiles import local_checks, suggest_profile
from .scoring import pass_codes
from .assessment_config import frozen_configuration,question_for_assessment
from .roles import role_context

def site_access(request, site_code, roles=None):
    site = get_object_or_404(Site, code=site_code)
    memberships = Membership.objects.filter(user=request.user, site=site)
    if not memberships.exists() or (roles and not memberships.filter(role__in=roles).exists()): raise Http404
    request.session['selected_site']=site.code
    return site

def active_assessment(site, user):
    draft = Assessment.objects.filter(site=site, status='draft').first()
    if draft: return draft
    previous = site.assessments.first()
    if previous: return previous
    raise Http404('No assessment is available for this site.')

def log(site, user, action, obj, detail=None):
    AuditEvent.objects.create(site=site, actor=user, action=action, object_type=type(obj).__name__, object_id=str(obj.pk), detail=detail or {})

@login_required
def home(request):
    site=selected_site(request)
    context={'site':site}
    if site:
        context.update(role_context(request.user,site))
        from .progress import coverage_progress
        context['progress']=coverage_progress(site)
        latest=site.assessments.first()
        codes,_=accepted_codes(site,latest)
        categories=Category.objects.prefetch_related('requirements')
        context['ready_sections']=sum(category_result({r.position:codes.get(r.code,'') for r in c.requirements.all()},latest.policy_version if latest else 'draft-v1')['earned'] is not None for c in categories)
        target={'C':5,'B':8,'A':10}[site.target_level]
        context['blockers']=Requirement.objects.filter(position__lte=target).exclude(code__in=[key for key,value in codes.items() if value in pass_codes(latest.policy_version if latest else 'draft-v1')])[:5]
        context['priority_actions']=Opportunity.objects.filter(site=site,status='open').order_by('-immediate_corrective','-prerequisite','due_date','pk')[:5]
        context['my_actions']=Opportunity.objects.filter(site=site,status='open',owner__iexact=request.user.username)[:5]
        context['upcoming_sessions']=AssessmentSession.objects.filter(site=site,date__gte=timezone.localdate()).order_by('date')[:3]
        context['active_improvements']=Kaizen.objects.filter(site=site).exclude(status='reassessment_accepted').order_by('-updated_at')[:3]
        context['my_improvements']=Kaizen.objects.filter(site=site,created_by=request.user).order_by('-updated_at')[:5]
        context['my_kaizen_actions']=KaizenAction.objects.filter(event__site=site).filter(Q(assignee__user=request.user)|Q(assignee__isnull=True,owner__iexact=request.user.username)).exclude(progress=100).select_related('event').order_by('end_date','pk')[:8]
        context['progress_choices']=(0,20,40,60,80,100)
        context['review_improvements']=Kaizen.objects.filter(site=site).order_by('-updated_at')[:5]
        context['advisory_followups']=Response.objects.filter(assessment=latest,code='A').select_related('requirement')[:5] if latest else []
    return render(request,'home.html',context)

@login_required
@require_POST
def switch_site(request):
    site=site_access(request,request.POST.get('site_code',''))
    area=request.POST.get('area','home')
    if area not in ('site','assessment','sessions','opportunities','kaizens','evidence','preparation','resources'): return redirect('home')
    return redirect(area,site_code=site.code)

@login_required
def locations(request):
    return render(request,'locations.html',{'sites':authorized_sites(request.user)})

@login_required
def resources(request,site_code):
    site=site_access(request,site_code)
    return render(request,'resources.html',{'site':site})

@login_required
def administration(request):
    sites=authorized_sites(request.user).filter(membership__user=request.user,membership__role='admin').distinct()
    if not sites.exists(): raise Http404
    return render(request,'administration.html',{'sites':sites})

@login_required
def site_progress(request, site_code):
    site = site_access(request, site_code)
    draft = site.assessments.filter(status='draft').first()
    approved = site.assessments.filter(status='approved').first()
    latest = draft or approved
    codes,unverified=accepted_codes(site,latest)
    dated={row['category']:row['result']['earned'] for row in approved.snapshot.get('categories',[])} if approved else {}
    rows = []
    for category in Category.objects.all():
        requirements = list(category.requirements.all())
        result = category_result({r.position:codes.get(r.code,'') for r in requirements},latest.policy_version if latest else 'draft-v1')
        blockers = [r for r in requirements if r.position <= {'C':5,'B':8,'A':10}[site.target_level] and codes.get(r.code) not in pass_codes(latest.policy_version if latest else 'draft-v1')]
        rows.append((category,result,dated.get(category.number),blockers))
    from .progress import coverage_progress
    return render(request, 'site.html', {'site':site,'latest':latest,'draft':draft,'approved':approved,'rows':rows,'unverified':unverified,'progress':coverage_progress(site)})

@login_required
def assessment(request, site_code):
    site = site_access(request, site_code)
    can_respond=Membership.objects.filter(user=request.user,site=site,role__in=['assessor','manager','admin']).exists()
    selected_id=request.GET.get('assessment','')
    if selected_id:
        if not selected_id.isdigit():raise Http404
        obj=get_object_or_404(Assessment,site=site,pk=int(selected_id))
    else:
        obj=site.assessments.filter(status='draft').first() or site.assessments.first()
        if obj is None:
            # Reading never creates a record; responders get a one-click start instead.
            return render(request,'assessment_start.html',{'site':site,'can_respond':can_respond,'sessions':AssessmentSession.objects.filter(site=site,availability='confirmed').order_by('-date')[:3]})
    query = request.GET.get('q','').strip()[:200]
    category = request.GET.get('category','')
    if category and (not category.isdigit() or not Category.objects.filter(number=int(category)).exists()):category=''
    answer = request.GET.get('answer','')
    if answer not in ('Y','A','N','unanswered'): answer=''
    evidence_type=request.GET.get('evidence_type','')
    if evidence_type not in ('document','observation','interview','audit'):evidence_type=''
    editable=obj.status=='draft' and can_respond
    view=request.GET.get('view','single' if editable else 'all')
    if view not in ('all','section','single'):view='all'
    from .progress import scope_for
    scope=scope_for(obj)
    reqs = Requirement.objects.filter(code__in=scope.get('requirements',[]))
    if view=='section' and not category:
        first=reqs.order_by('category_id').first()
        category=str(first.category_id) if first else ''
    if category.isdigit(): reqs = reqs.filter(category_id=int(category))
    if query: reqs = reqs.filter(Q(code__icontains=query)|Q(detail_text__icontains=query)|Q(expected_evidence__icontains=query))
    if evidence_type:
        reqs=reqs.filter(code__in=Coverage.objects.filter(evidence__site=site,evidence__evidence_type=evidence_type).values_list('clause__requirement_id',flat=True))
    if answer:
        answered_ids=obj.responses.filter(code__in=('Y','A','N')).values_list('requirement_id',flat=True)
        reqs=reqs.exclude(code__in=answered_ids) if answer=='unanswered' else reqs.filter(code__in=obj.responses.filter(code=answer).values_list('requirement_id',flat=True))
    paginator=Paginator(reqs,1 if view=='single' else 10 if view=='section' else 20)
    page_number=request.GET.get('page')
    answered=set(obj.responses.filter(code__in=('Y','A','N')).values_list('requirement_id',flat=True))
    if view=='single' and not page_number and editable:
        # Resume at the first unanswered question in the current filter.
        ordered=list(reqs.values_list('code',flat=True))
        first_open=next((i for i,code in enumerate(ordered) if code not in answered),0)
        page_number=first_open+1
    page = paginator.get_page(page_number)
    rows = {r.requirement_id:r for r in obj.responses.filter(requirement__in=page.object_list)}
    pending=set(obj.responses.filter(advisory_retest_status='pending').values_list('requirement_id',flat=True))
    prior=site.assessments.filter(status='approved',version__lt=obj.version).order_by('-version').first()
    prior_rows={r.requirement_id:r for r in prior.responses.filter(requirement__in=page.object_list)} if prior else {}
    from .readiness import evidence_state
    evidence=evidence_state(site,[req for req in page.object_list])
    for req in page.object_list:
        row=rows.get(req.code)
        req.response=row
        req.response_code = row.code if row else ''
        req.local_question=question_for_assessment(obj,req)
        req.needs_retest=req.code in pending
        req.prior=prior_rows.get(req.code)
        req.evidence=evidence.get(req.code)
        req.level_label={'C':'Certified','B':'Advanced','A':'Showcase'}.get(req.level_code,'')
    scope_codes=scope.get('requirements',[])
    context_extra={'editable':editable,'can_respond':can_respond,'prior':prior,
                   'answered_count':len(answered&set(scope_codes)),'scope_count':len(scope_codes),
                   'next_open':next((code for code in scope_codes if code not in answered),None)}
    context={'site':site,'assessment':obj,'page':page,'query':query,'category':category,'answer':answer,
             'evidence_type':evidence_type,'view':view,'scope':scope,
             'filters_active':bool(query or (category and view!='section') or answer or evidence_type),
             'section':Category.objects.filter(number=int(category)).first() if view=='section' and category.isdigit() else None,
             'section_prev':Category.objects.filter(number__lt=int(category)).order_by('-number').first() if view=='section' and category.isdigit() else None,
             'section_next':Category.objects.filter(number__gt=int(category)).order_by('number').first() if view=='section' and category.isdigit() else None,
             'categories':Category.objects.all(),'assessments':site.assessments.all(),
             'history':site.assessments.all(),**context_extra}
    return render(request,'assessment_results.html' if request.headers.get('HX-Request')=='true' else 'assessment.html',context)

@login_required
def respond(request, site_code, req_code):
    site = site_access(request,site_code)
    can_respond=Membership.objects.filter(user=request.user,site=site,role__in=['assessor','manager','admin']).exists()
    if request.method=='POST' and not can_respond: raise Http404
    req = get_object_or_404(Requirement.objects.prefetch_related('clauses'),code=req_code)
    selected_id=request.POST.get('assessment_id') if request.method=='POST' else request.GET.get('assessment')
    if selected_id:
        if not str(selected_id).isdigit():raise Http404
        obj=get_object_or_404(Assessment,site=site,pk=int(selected_id))
    else:
        try:obj = active_assessment(site,request.user)
        except Http404:
            if can_respond:raise
            obj = None  # Read-only global question remains visible before the first assessment.
    from .progress import scope_for
    if obj and req.code not in scope_for(obj).get('requirements',[]):raise Http404
    existing = Response.objects.filter(assessment=obj,requirement=req).first() if obj else None
    prior=site.assessments.filter(status='approved',version__lt=obj.version).order_by('-version').first() if obj else None
    previous_advisory=Response.objects.filter(assessment=prior,requirement=req,code='A').first() if prior else None
    next_req=Requirement.objects.filter(code__in=scope_for(obj).get('requirements',[])).filter(
        Q(category_id__gt=req.category_id)|Q(category_id=req.category_id,position__gt=req.position)).first()
    previous_evidence=[]
    if previous_advisory and prior.snapshot:
        from .access import allowed_classifications
        visible_ids=set(Evidence.objects.filter(site=site,classification__in=allowed_classifications(request.user,site)).values_list('pk',flat=True))
        clause_ids=set(req.clauses.values_list('id',flat=True))
        previous_evidence=list(dict.fromkeys(row['evidence_title'] for row in prior.snapshot.get('coverage',[])
            if row['clause_id'] in clause_ids and row.get('evidence_id') in visible_ids))
    from .assessment_config import preparation_for_assessment
    from urllib.parse import urlencode
    back_values=request.GET
    back_query=urlencode({key:back_values.get(key,'') for key in ('view','category','q','answer','evidence_type','page')
        if back_values.get(key,'')})
    if obj:back_query=urlencode({'assessment':obj.pk})+('&'+back_query if back_query else '')
    coverage=Coverage.objects.filter(evidence__site=site,clause__requirement=req).select_related('evidence','clause')
    if not can_respond: coverage=coverage.filter(evidence__classification='internal')
    response_context={'site':site,'req':req,'assessment':obj,'response':existing,'next_req':next_req,'can_respond':can_respond,'coverage':coverage,
                      'question':question_for_assessment(obj,req),'preparation_need':preparation_for_assessment(obj,req),
                      'previous_advisory':previous_advisory,'previous_evidence':previous_evidence,'back_query':back_query,
                      'needs_retest':bool(existing and existing.advisory_retest_status=='pending'),
                      'related_actions':Opportunity.objects.filter(site=site,requirement=req).order_by('-id')[:10],
                      'related_kaizens':Kaizen.objects.filter(site=site,linked_requirements=req).distinct().order_by('-updated_at')[:10]}
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                obj = Assessment.objects.select_for_update().get(pk=obj.pk)
                if obj.status != 'draft': return HttpResponseForbidden('Approved records are immutable.')
                if obj.revision != form.cleaned_data['revision']:
                    form.add_error(None,'Another edit was saved. Reload and review the latest response.')
                    if request.POST.get('autosave')=='1':
                        return JsonResponse({'saved':False,'errors':form.errors},status=409)
                else:
                    code=form.cleaned_data['code']
                    if response_context['needs_retest'] and not form.cleaned_data['retest_confirm']:
                        form.add_error('retest_confirm','Record an explicit retest of the previous Advisory before changing this answer.')
                    if form.errors:
                        if request.POST.get('autosave')=='1':return JsonResponse({'saved':False,'errors':form.errors},status=409 if form.non_field_errors() else 422)
                        return render(request,'respond.html',{**response_context,'form':form})
                    retested=response_context['needs_retest'] or response_context['previous_advisory'] is not None
                    retest_status=('due_next' if code=='A' and obj.policy_version=='advisory-v2' else
                                   'retested' if retested and code in ('Y','N') else 'not_due')
                    defaults={'code':code,'advisory_retest_status':retest_status,'updated_by':request.user}
                    # A compact answer control posts only the code; keep text the auditor wrote elsewhere.
                    if 'conclusion' in request.POST: defaults['conclusion']=form.cleaned_data['conclusion']
                    if code!='A': defaults['advisory_follow_up']=''
                    elif 'advisory_follow_up' in request.POST: defaults['advisory_follow_up']=form.cleaned_data['advisory_follow_up']
                    Response.objects.update_or_create(assessment=obj,requirement=req,defaults=defaults)
                    obj.revision += 1; obj.save(update_fields=['revision'])
                    log(site,request.user,'response_saved',req,{'code':form.cleaned_data['code'],'assessment':obj.pk})
                    if request.POST.get('autosave')=='1':return JsonResponse({'saved':True,'revision':obj.revision,'message':f'{req.code} saved.'})
                    messages.success(request,f'{req.code} saved.')
                    if request.POST.get('go')=='next' and next_req:
                        target=redirect('respond',site_code=site.code,req_code=next_req.code)
                        if selected_id:target['Location']+=f'?assessment={obj.pk}'
                        return target
                    target=redirect('assessment',site_code=site.code)
                    if selected_id or request.GET:target['Location']+='?'+back_query
                    return target
        elif request.POST.get('autosave')=='1':return JsonResponse({'saved':False,'errors':form.errors},status=422)
    else:
        form = ResponseForm(initial={'code':existing.code if existing else '', 'conclusion':existing.conclusion if existing else '',
                                     'advisory_follow_up':existing.advisory_follow_up if existing else '', 'revision':obj.revision if obj else 0})
    return render(request,'respond.html',{**response_context,'form':form})

@login_required
@require_POST
def approve(request,site_code):
    site=site_access(request,site_code,['manager','admin'])
    with transaction.atomic():
        obj=Assessment.objects.select_for_update().filter(site=site,status='draft').first()
        if not obj: raise Http404
        from .assessment_rules import approval_problems
        problems=approval_problems(site,obj,allow_unanswered=request.POST.get('confirm_partial')=='on')
        if problems:
            for problem in problems: messages.error(request,problem)
            return redirect(reverse('assessment',args=[site.code])+f'?assessment={obj.pk}')
        obj.status='approved'; obj.approved_by=request.user; obj.approved_at=timezone.now(); obj.rationale=request.POST.get('rationale',''); obj.save()
        obj.snapshot=assessment_snapshot(site,obj);obj.save(update_fields=['snapshot'])
        log(site,request.user,'local_snapshot_approved',obj,{'policy':obj.policy_version})
    messages.success(request,'Dated local assessment saved. Draft scoring policy is unapproved; this is not an official certification.')
    return redirect('site',site_code=site.code)

@login_required
@require_POST
def new_draft(request,site_code):
    from .progress import scope_for
    site=site_access(request,site_code,['assessor','manager','admin'])
    plan_id=request.POST.get('session_id','')
    plan=get_object_or_404(AssessmentSession,site=site,pk=int(plan_id)) if plan_id.isdigit() else None
    if plan_id and not plan:raise Http404
    if plan and plan.availability!='confirmed':return HttpResponse('Resolve manager availability before starting this planned assessment.',status=422)
    with transaction.atomic():
        if not site.assessments.filter(status='draft').exists():
            previous=site.assessments.first()
            obj=Assessment.objects.create(site=site,version=previous.version+1 if previous else 1,created_by=request.user,
                planned_session=plan,rationale=request.POST.get('rationale',''),scope_snapshot=scope_for(previous),configuration_snapshot=frozen_configuration(site))
            log(site,request.user,'new_draft',obj,{'from':previous.pk if previous else None})
        else: messages.info(request,'An editable draft already exists with its own frozen snapshot; open it before scheduling a new version.')
    return redirect('assessment',site_code=site.code)

@login_required
def opportunities(request,site_code):
    site=site_access(request,site_code)
    form=OpportunityForm(request.POST or None)
    if request.method=='POST':
        site_access(request,site_code,['assessor','manager','admin','staff'])
        if form.is_valid():
            if form.cleaned_data.get('priority_override') is not None and not Membership.objects.filter(user=request.user,site=site,role__in=['manager','admin']).exists():
                form.add_error('priority_override','Only a site manager may override the suggested order.')
        if form.is_valid():
            obj=form.save(commit=False);obj.site=site;obj.save();log(site,request.user,'opportunity_created',obj)
            messages.success(request,'Opportunity saved. A Kaizen requires separate acceptance.')
            return redirect('opportunities',site_code=site.code)
    items=list(Opportunity.objects.filter(site=site).select_related('requirement'))
    current=site.assessments.first()
    codes,_=accepted_codes(site,current)
    limit={'C':5,'B':8,'A':10}[site.target_level]
    for item in items:
        item.target_blocker=bool(item.requirement and item.requirement.position<=limit and codes.get(item.requirement_id) not in pass_codes(current.policy_version if current else 'draft-v1'))
        item.sequence_reason=('Immediate corrective need' if item.immediate_corrective else
                              'Blocker for target level' if item.target_blocker else
                              'Prerequisite' if item.prerequisite else 'Other opportunity')
    items.sort(key=lambda x:(x.priority_override if x.priority_override is not None else 100,
                             0 if x.immediate_corrective else 1,0 if x.target_blocker else 1,
                             0 if x.prerequisite else 1,x.due_date or date.max,x.id))
    from .matrix import assessment_matrix
    matrix=assessment_matrix(current)
    matrix_section=request.GET.get('section','')
    if not matrix_section.isdigit() or int(matrix_section) not in {category.number for category in matrix['categories']}:
        matrix_section=''
    matrix_state=request.GET.get('state','')
    if matrix_state not in ('yes','advisory','no','unanswered'):
        matrix_state=''
    matrix_query=request.GET.get('q','').strip()[:200]
    if matrix_section.isdigit():
        matrix['rows']=[row for row in matrix['rows'] if row['category'].number==int(matrix_section)]
    if matrix_state in ('yes','advisory','no','unanswered') or matrix_query:
        matrix['rows']=[row for row in matrix['rows'] if any(cell['requirement'] and
            (not matrix_state or cell['state']==matrix_state) and
            (not matrix_query or matrix_query.casefold() in cell['requirement'].code.casefold() or
             matrix_query.casefold() in cell['requirement'].detail_text.casefold()) for cell in row['cells'])]
    return render(request,'opportunities.html',{'site':site,'items':items,'form':form,'matrix':matrix,
        'matrix_section':matrix_section,'matrix_state':matrix_state,'matrix_query':matrix_query,
        'matrix_filters_active':bool(matrix_section or matrix_state or matrix_query)})

@login_required
def sessions(request,site_code):
    site=site_access(request,site_code)
    form=SessionForm(request.POST or None)
    if request.method=='POST':
        site_access(request,site_code,['assessor','manager','admin'])
        if form.is_valid():
            obj=form.save(commit=False);obj.site=site;obj.time_blocks=form.cleaned_data['blocks_text'];obj.save();form.save_m2m()
            from .journey_views import _session_state
            from .models import SessionRevision
            SessionRevision.objects.create(session=obj,revision=0,actor=request.user,reason='Initial assessment plan',
                after=_session_state(obj))
            log(site,request.user,'session_created',obj)
            messages.success(request,'Proposed plan saved. Ask the site manager to confirm availability or suggest an alternative.')
            return redirect('session_detail',site_code=site.code,pk=obj.pk)
    return render(request,'sessions.html',{'site':site,'form':form,
        'can_plan':Membership.objects.filter(site=site,user=request.user,role__in=['assessor','manager','admin']).exists(),
        'items':AssessmentSession.objects.filter(site=site).order_by('-date')})

@login_required
def kaizens(request,site_code):
    site=site_access(request,site_code)
    finding=Opportunity.objects.filter(site=site,pk=request.GET.get('finding')).first() if request.GET.get('finding','').isdigit() else None
    requirement=Requirement.objects.filter(code=request.GET.get('requirement','')).first() or (finding.requirement if finding else None)
    form=KaizenForm(request.POST or None,initial={'owner':request.user.username,'process_location':site.name,
                                                'opportunity':finding,'title':finding.problem[:190] if finding else '',
                                                'requirement':requirement.code if requirement else ''})
    form.fields['opportunity'].queryset=Opportunity.objects.filter(site=site)
    if request.method=='POST':
        site_access(request,site_code,['staff','coach','manager','admin'])
        if form.is_valid():
            obj=form.save(commit=False);obj.site=site;obj.created_by=request.user
            obj.data={'overall_problem':obj.title,'owner':form.cleaned_data['owner'] or request.user.username,
                      'process_location':form.cleaned_data['process_location'] or site.name,
                      'due_date':form.cleaned_data['due_date'].isoformat() if form.cleaned_data['due_date'] else ''}
            if form.cleaned_data['specific_problem'].strip(): obj.data['specific_problem']=form.cleaned_data['specific_problem'].strip()
            obj.data['profile_suggestion'],obj.data['profile_suggestion_reason']=form.suggestion()
            obj.save()
            linked=obj.opportunity.requirement if obj.opportunity and obj.opportunity.requirement else Requirement.objects.filter(code=form.cleaned_data['requirement']).first()
            if linked: obj.linked_requirements.add(linked)
            # The creator leads the team by default; this is not an approval or a source authority.
            Participant.objects.create(event=obj,user=request.user,first_initial=(request.user.first_name[:1] or request.user.username[:1]).upper(),
                                       last_name=request.user.last_name or request.user.username,kaizen_role='Kaizen lead')
            checkpoint(obj,request.user,'Draft created')
            log(site,request.user,'kaizen_accepted',obj)
            return redirect(reverse('kaizen_detail',args=[site.code,obj.pk])+'?created=1')
    items=list(Kaizen.objects.filter(site=site).prefetch_related('linked_requirements').order_by('-updated_at'))
    state=request.GET.get('state','')
    if state not in REVIEW_STATE_LABELS: state=''
    cards=[]
    for event in items:
        current=review_state(event)
        if state and current!=state: continue
        cards.append({'event':event,'state':current,'state_label':REVIEW_STATE_LABELS[current],'gates':gate_summary(event),'segments':pdca_segments(event)})
    suggestion=form.suggestion() if form.is_bound else None
    return render(request,'kaizens.html',{'site':site,'cards':cards,'form':form,'state':state,'states':REVIEW_STATE_LABELS,'linked_requirement':requirement,
                  'suggestion':suggestion,'show_form':request.GET.get('new')=='1' or form.is_bound or bool(finding or requirement),
                  'can_create':Membership.objects.filter(user=request.user,site=site,role__in=['staff','coach','manager','admin']).exists()})

@login_required
def kaizen_detail(request,site_code,pk):
    site=site_access(request,site_code)
    obj=get_object_or_404(Kaizen,pk=pk,site=site)
    if request.method=='POST':
        site_access(request,site_code,['coach','manager','admin','staff'])
        require_event_editor(request.user,obj)
        form=KaizenStageForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                obj=Kaizen.objects.select_for_update().get(pk=obj.pk)
                if obj.revision != form.cleaned_data['revision']:
                    form.add_error(None,'Another edit was saved. Reload and review the latest event.')
                else:
                    before=snapshot(obj)
                    can_review=Membership.objects.filter(user=request.user,site=site,role__in=['coach','manager','admin']).exists()
                    edits={k:(v.isoformat() if isinstance(v,date) else str(v) if v is not None else '') for k,v in form.cleaned_data.items() if k!='revision' and k in request.POST}
                    if not can_review and any(k in REVIEW_KEYS and obj.data.get(k,'')!=v for k,v in edits.items()):
                        form.add_error(None,'Sensei review fields can only be changed by a coach or site manager.')
                    changed=any(obj.data.get(k,'')!=v for k,v in edits.items())
                    obj.data={**obj.data,**edits}
                    if changed: reopen_after_change(obj)
                    action=request.POST.get('action','save')
                    if action=='close_local':
                        missing=local_checks(obj)
                        if missing: form.add_error(None,'Before local closure: '+', '.join(missing))
                        else: obj.local_status='closed'
                    elif action=='submit_review':
                        # Open sensei requests are resolved by the sensei at finalisation, so they do not block a resubmission.
                        missing=[gate['label'] for gate in gate_summary(obj)['gates'] if not gate['ok'] and gate['key']!='requests']
                        if missing: form.add_error(None,'Before submitting: '+', '.join(missing))
                        else: obj.status='results_under_review';obj.submitted_at=timezone.now()
                    elif action=='request_reassessment':
                        if obj.status not in ('verified','sustained'):
                            form.add_error(None,'Coach verification is required before reassessment can be requested.')
                        else: obj.status='reassessment_pending'
                    elif action=='accept_reassessment':
                        if not Membership.objects.filter(user=request.user,site=site,role__in=['manager','admin']).exists():
                            form.add_error(None,'Site manager authority is required.')
                        elif obj.status!='reassessment_pending':
                            form.add_error(None,'A reassessment must be pending first.')
                        else:
                            approved=site.assessments.filter(status='approved').first()
                            accepted,_=accepted_codes(site,approved)
                            linked=list(obj.linked_requirements.values_list('code',flat=True))
                            if not linked or not approved or any(accepted.get(code) not in pass_codes(approved.policy_version) for code in linked):
                                form.add_error(None,'Every linked requirement needs a current evidence-supported pass in an approved dated assessment.')
                            else: obj.status='reassessment_accepted'
                    elif action=='verify':
                        if not Membership.objects.filter(user=request.user,site=site,role__in=['coach','manager','admin']).exists():
                            form.add_error(None,'Coach or manager authority is required.')
                        elif obj.status != 'results_under_review':
                            form.add_error(None,'Move through Plan, Do, implementation, and results review before verification.')
                        elif any(not obj.data.get(k) for k in ('overall_problem','specific_problem','solution','baseline','actual','unit','population','data_source','coach_review','sustain')):
                            form.add_error(None,'Complete the problem, solution, comparable measure, data source, sustain plan, and coach review before verification.')
                        elif not any(c['difference'] is not None for c in compare_observations(obj.observations.all())):
                            form.add_error(None,'Record comparable before and after observations before verification.')
                        elif not obj.actions.filter(phase='DO').exists() or not obj.actions.filter(phase='ACT').exists():
                            form.add_error(None,'Record at least one Do action and one Act sustain action before verification.')
                        elif obj.data.get('star_7')=='Y' and not results_criterion(obj.data,list(obj.observations.all())):
                            form.add_error(None,'Star 7 cannot be confirmed: comparable results must span more than 30 days and five after points, with target met or a follow-up action.')
                        elif obj.data.get('star_8')=='Y' and document_type_count(obj)<2:
                            form.add_error(None,'Star 8 cannot be confirmed without two different document or site-tool types.')
                        elif obj.review_notes.filter(kind__in=['clarify','return'],resolved=False).exists():
                            form.add_error(None,'Resolve the outstanding sensei requests before verification.')
                        else: obj.status='verified'
                    elif action=='advance':
                        order=['proposed','planned','in_progress','implemented','results_under_review']
                        if obj.status in order:
                            from .methodology import cause_analysis_required
                            needed={'proposed':('overall_problem','specific_problem')+(('root_cause',) if cause_analysis_required(obj) else ()), 'planned':('solution',),
                                    'in_progress':('solution',), 'implemented':('baseline','actual','unit','population','data_source')}.get(obj.status,())
                            if any(not obj.data.get(k) for k in needed): form.add_error(None,'Complete the current PDCA fields before advancing.')
                            elif obj.status=='results_under_review': form.add_error(None,'Coach verification is required before sustain status.')
                            else: obj.status=order[min(order.index(obj.status)+1,len(order)-1)]
                        elif obj.status=='verified':
                            if not obj.actions.filter(phase='ACT').exists() or not obj.document_updates.exists():
                                form.add_error(None,'Sustain status needs an Act action and a document or site-tool update.')
                            else: obj.status='sustained'
                    if form.errors:
                        obj.refresh_from_db()
                    else:
                        checkpoint(obj,request.user,'Before edit or transition',before)
                        obj.revision+=1;obj.save();log(site,request.user,'kaizen_saved',obj,{'status':obj.status})
                        checkpoint(obj,request.user,'Saved '+action)
                        if action=='close_local' or (action in ('verify','advance','accept_reassessment') and obj.status in ('verified','sustained','reassessment_accepted')):
                            from .a3 import ensure_reports
                            ensure_reports(obj,request.user)
                        messages.success(request,'Kaizen saved. Linked TCA responses were not changed.')
                        return redirect(request.path+'?stage='+request.POST.get('workspace_stage','Plan') if request.POST.get('workspace_stage') in ('Plan','Do','Check','Act') else request.path)
    else: form=KaizenStageForm(initial={**obj.data,'revision':obj.revision})
    return render_kaizen(request,site,obj,form)

def render_kaizen(request,site,obj,form,child_forms=None):
    from .access import visible_attachments
    from .methodology import rules_for
    active_phase=request.GET.get('stage') or request.POST.get('workspace_stage') or current_phase(obj)
    if active_phase not in ('Plan','Do','Check','Act'): active_phase='Plan'
    phase_code={'Plan':'PLN','Do':'DO','Check':'CHK','Act':'ACT'}[active_phase]
    children={'action_form':ActionForm(event=obj,auto_id='id_action_%s',initial={'phase':phase_code}),'observation_form':ObservationForm(auto_id='id_observation_%s',initial={'measure':obj.data.get('measure'),'unit':obj.data.get('unit'),'population':obj.data.get('population'),'data_source':obj.data.get('data_source')}),
              'benefit_form':BenefitForm(auto_id='id_benefit_%s'),'participant_form':ParticipantForm(auto_id='id_participant_%s'),
              'document_form':DocumentUpdateForm(auto_id='id_document_%s'),'member_form':TeamMemberForm(event=obj,auto_id='id_member_%s')}
    children.update(child_forms or {})
    quality={'results_over_30_days_and_5_points':results_criterion(obj.data,list(obj.observations.all())),
             'two_document_types':document_type_count(obj)>=2}
    star_count=sum(obj.data.get(f'star_{i}')=='Y' for i in range(1,11))
    financial_access=Membership.objects.filter(user=request.user,site=site,role__in=['assessor','manager','admin']).exists()
    participant_access=Membership.objects.filter(user=request.user,site=site,role__in=['assessor','coach','manager','admin']).exists()
    participants=list(obj.participants.select_related('user'))
    unique_participants=len({('user',p.user_id) if p.user_id else (p.email.lower() if p.email else (p.first_initial.lower(),p.last_name.lower())) for p in participants})
    phases=[('Plan','Define the problem and the intended result.', ['overall_problem','outcome_criterion','specific_problem','root_cause','cause_status','measure','baseline','target','unit','population','direction']),
            ('Do','Record the countermeasure and implementation.', ['solution']),
            ('Check','Compare equivalent results and retain the data source.', ['observed_result','result_date','actual','result_period_start','result_period_end','data_points','data_source']),
            ('Act','Record sustain work and any further improvement.', ['sustain','sustain_owner','sustain_check','document_types','next_kaizen_action'])]
    previous,changes=changed_since_review(obj)
    review_access=Membership.objects.filter(user=request.user,site=site,role__in=['coach','manager','admin']).exists()
    phase_forms=[{'title':title,'help':help_text,'fields':[form[key] for key in keys],
                  'open':title==active_phase or any(form[key].errors for key in keys)} for title,help_text,keys in phases]
    if obj.input_profile=='small':
        basic={'overall_problem','outcome_criterion','solution','observed_result','result_date','sustain','sustain_owner','sustain_check'}
        for phase in phase_forms:
            phase['extra_fields']=[f for f in phase['fields'] if f.name not in basic]
            phase['fields']=[f for f in phase['fields'] if f.name in basic]
            phase['open']=True
    actions=list(obj.actions.select_related('assignee__user').order_by('start_date','pk'))
    edit_actions=[{'record':action,'form':children.get('edit_action_form') if children.get('edit_action_id')==action.pk else ActionForm(event=obj,instance=action,auto_id=f'id_action_{action.pk}_%s')} for action in actions]
    gates=gate_summary(obj);state=review_state(obj)
    anchors={'do_action':'actions','act_action':'actions','observations':'observations','requests':'review','star_7':'review','star_8':'review'}
    for gate in gates['gates']: gate['anchor']=anchors.get(gate['key'],'id_'+gate['key'])
    can_edit=can_edit_event(request.user,obj)
    missing=[gate for gate in gates['gates'] if not gate['ok'] and gate['key']!='requests']
    view=request.GET.get('view','table')
    return render(request,'kaizen_detail.html',{'site':site,'event':obj,'form':form,'quality':quality,'star_count':star_count,
        'phase_forms':phase_forms,'active_phase':active_phase,'local_checks':local_checks(obj),'attachments':visible_attachments(obj,request.user),
        'edit_actions':edit_actions,'working_summary':[(title,obj.data.get(key,'')) for title,key in [('Problem','overall_problem'),('Specific problem','specific_problem'),('Cause investigation','root_cause'),('Countermeasure','solution'),('Result','actual'),('Sustain / learning','sustain_check')]],
        'context_fields':[form[k] for k in ('owner','process_location','due_date')],
        'review_fields':[form[k] for k in REVIEW_KEYS] if review_access else [],'review_access':review_access,
        'review_form':children.get('bound_review_form') or ReviewNoteForm(initial={'stage':active_phase,'revision':obj.revision},auto_id='id_review_%s'),
        'review_checks':review_checks(obj),'previous_review':previous,'review_changes':changes,
        'measurement_warnings':measurement_warnings(obj),'can_edit':can_edit,'can_manage_team':can_manage_team(request.user,obj),
        'gates':gates,'next_gate':missing[0] if missing else None,'state':state,'state_label':REVIEW_STATE_LABELS[state],
        'segments':pdca_segments(obj),'method_rules':rules_for(obj.profile),'created':request.GET.get('created')=='1',
        'open_returns':obj.review_notes.filter(kind='return',resolved=False).select_related('actor'),
        'team':[{'record':p,'name':team_display(p),'initials':initials(team_display(p)),'role':p.kaizen_role,'is_me':p.user_id==request.user.pk} for p in participants],
        'gantt':gantt(actions,timezone.localdate()),'actions_view':'gantt' if view=='gantt' else 'table',
        'next_action':{'Plan':'Define the specific problem and measure, then move to Do.','Do':'Record implementation actions and dates, then check the result.','Check':'Record comparable observations, then plan how to sustain the change.','Act':'Record standardization and sustain checks, then submit the prepared work for sensei review.'}[active_phase],
        'notes':obj.review_notes.select_related('actor','reply_to'),'history':obj.history.all()[:15],
        **children,'unique_participants':unique_participants,
        'visible_participants':participants if participant_access else [],'participant_access':participant_access,
        'comparisons':_with_bars(compare_observations(obj.observations.all())),'visible_benefits':obj.benefits.all() if financial_access else [],
        'financial_access':financial_access,'benefit_totals':event_benefits(obj.benefits.all()) if financial_access else {}})

def _with_bars(rows):
    for row in rows:
        if row['before_average'] is not None and row['after_average'] is not None:
            top=max(abs(row['before_average']),abs(row['after_average'])) or 1
            row['before_pct']=round(float(abs(row['before_average'])/top*100),1);row['after_pct']=round(float(abs(row['after_average'])/top*100),1)
    return rows

@login_required
@require_POST
def kaizen_autosave(request,site_code,pk):
    site=site_access(request,site_code,['staff','coach','manager','admin'])
    with transaction.atomic():
        event=get_object_or_404(Kaizen.objects.select_for_update(),site=site,pk=pk)
        if not can_edit_event(request.user,event): return JsonResponse({'message':'Only the event team can change this Kaizen.'},status=403)
        # Validate against saved dates as well as the edited fields, without replacing unsubmitted values.
        combined={**event.data,**request.POST.dict()}
        form=KaizenStageForm(combined)
        if not form.is_valid(): return JsonResponse({'errors':form.errors.get_json_data()},status=422)
        if event.revision!=form.cleaned_data['revision']:
            return JsonResponse({'message':'Another edit was saved. Your entries remain here; reload the latest version before retrying.'},status=409)
        edits={key:(value.isoformat() if isinstance(value,date) else str(value) if value is not None else '')
               for key,value in form.cleaned_data.items() if key!='revision' and key in request.POST}
        review_access=Membership.objects.filter(user=request.user,site=site,role__in=['coach','manager','admin']).exists()
        if not review_access and any(key in REVIEW_KEYS and event.data.get(key,'')!=value for key,value in edits.items()):
            return JsonResponse({'message':'Sensei review fields require coach authority.'},status=403)
        if any(event.data.get(key,'')!=value for key,value in edits.items()):
            checkpoint(event,request.user,'Before autosave')
            event.data={**event.data,**edits};reopen_after_change(event)
            event.revision+=1;event.save()
            checkpoint(event,request.user,'Autosaved participant work')
            log(site,request.user,'kaizen_autosaved',event,{'revision':event.revision})
        return JsonResponse({'revision':event.revision,'saved_at':event.updated_at.isoformat(),'status':event.status,'local_status':event.local_status})

@login_required
def review_queue(request,site_code):
    site=site_access(request,site_code,['coach','manager','admin'])
    from django.db.models.functions import Coalesce
    form=ReviewQueueForm(request.GET or None)
    rows=[];counts={key:0 for key in REVIEW_STATE_LABELS}
    filters=form.cleaned_data if form.is_bound and form.is_valid() else {}
    state=filters.get('state') or ('all' if filters.get('scope')=='all' else 'submitted')
    # Most recently submitted first; never-submitted work follows by latest change.
    events=Kaizen.objects.filter(site=site).exclude(status='reassessment_accepted').annotate(
        last_submitted=Coalesce('submitted_at','updated_at')).order_by('-last_submitted','-pk')
    if filters.get('q'): events=events.filter(Q(title__icontains=filters['q'])|Q(pk__in=[int(x) for x in [filters['q'].upper().replace('KZ-','')] if x.isdigit()]))
    if not form.is_bound or form.is_valid():
        for event in events:
            current=review_state(event);counts[current]+=1
            if state!='all' and current!=state: continue
            stage=current_phase(event)
            if filters.get('stage') and stage!=filters['stage']: continue
            if filters.get('due'):
                try:
                    if date.fromisoformat(event.data.get('due_date',''))>filters['due']: continue
                except ValueError: continue
            missing=review_checks(event);gates=gate_summary(event);previous,changes=changed_since_review(event)
            if filters.get('readiness')=='ready' and missing: continue
            if filters.get('readiness')=='missing' and not missing: continue
            rows.append({'event':event,'stage':stage,'missing':missing,'changes':changes,'gates':gates,'state':current,'state_label':REVIEW_STATE_LABELS[current]})
    query=request.GET.copy();query.pop('page',None);query.pop('state',None);query.pop('scope',None)
    return render(request,'review_queue.html',{'site':site,'form':form,'rows':Paginator(rows,20).get_page(request.GET.get('page')),
        'state':state,'counts':counts,'states':[('submitted','Submitted'),('returned','Sensei feedback'),('in_progress','In progress'),('finalised','Finalised'),('all','All')],
        'base_query':query.urlencode(),'filters_active':bool(filters.get('stage') or filters.get('due') or filters.get('readiness') or filters.get('q'))})

@login_required
@require_POST
def review_note(request,site_code,pk):
    site=site_access(request,site_code,['staff','coach','manager','admin'])
    is_sensei=Membership.objects.filter(user=request.user,site=site,role__in=['coach','manager','admin']).exists()
    if not is_sensei and not request.POST.get('reply_to'): raise Http404
    with transaction.atomic():
        event=get_object_or_404(Kaizen.objects.select_for_update(),site=site,pk=pk)
        if not is_sensei: require_event_editor(request.user,event)
        if request.POST.get('revision')!=str(event.revision):
            response=review_failure(request,site,event,'Another edit was saved. Your message is retained; review the refreshed record before retrying.')
            response.status_code=409;return response
        if request.POST.get('resolve'):
            if not is_sensei: raise Http404
            note=get_object_or_404(ReviewNote,pk=request.POST['resolve'],event=event,kind__in=['clarify','return'])
            checkpoint(event,request.user,'Before request resolution')
            note.resolved=True;note.resolved_by=request.user;note.resolved_at=timezone.now();note.save()
        elif request.POST.get('reply_to'):
            parent=get_object_or_404(ReviewNote,pk=request.POST['reply_to'],event=event)
            text=request.POST.get('text','').strip()
            if not text or len(text)>10000:
                response=review_failure(request,site,event,'Enter a reply of at most 10000 characters. Your text is retained.')
                response.status_code=422;return response
            checkpoint(event,request.user,'Before team reply')
            ReviewNote.objects.create(event=event,stage=parent.stage,kind='reply',text=text,actor=request.user,event_revision=event.revision,reply_to=parent)
        else:
            if not is_sensei: raise Http404
            form=ReviewNoteForm(request.POST,auto_id='id_review_%s')
            if not form.is_valid():
                context_form=KaizenStageForm(initial={**event.data,'revision':event.revision})
                return render_kaizen(request,site,event,context_form,{'bound_review_form':form})
            checkpoint(event,request.user,'Before sensei advice')
            ReviewNote.objects.create(event=event,stage=form.cleaned_data['stage'],kind=form.cleaned_data['kind'],text=form.cleaned_data['text'],actor=request.user,event_revision=event.revision)
            if form.cleaned_data['kind']=='clarify': reopen_after_change(event)
            if form.cleaned_data['kind']=='return': event.status='in_progress'
        event.revision+=1;event.save();checkpoint(event,request.user,'Review conversation updated')
        log(site,request.user,'kaizen_review_note',event)
    messages.success(request,'Review advice saved with the event. TCA responses remain separate.')
    from django.urls import reverse
    stage=request.POST.get('workspace_stage') or request.POST.get('stage')
    if request.POST.get('next')=='review' and is_sensei: return redirect('kaizen_review_detail',site_code=site.code,pk=event.pk)
    url=reverse('kaizen_detail',args=[site.code,event.pk])
    return redirect(url+'?stage='+stage if stage in ('Plan','Do','Check','Act') else url)

def review_failure(request,site,event,message):
    children={'conversation_error':message}
    if request.POST.get('reply_to'):
        parent=get_object_or_404(ReviewNote,pk=request.POST['reply_to'],event=event)
        children.update({'reply_draft_id':parent.pk,'reply_draft_text':request.POST.get('text','')})
    elif not request.POST.get('resolve'):
        data=request.POST.copy();data['revision']=str(event.revision)
        note_form=ReviewNoteForm(data,auto_id='id_review_%s');note_form.add_error(None,message)
        children['bound_review_form']=note_form
    return render_kaizen(request,site,event,KaizenStageForm(initial={**event.data,'revision':event.revision}),children)

@login_required
@require_POST
def kaizen_action_edit(request,site_code,pk,action_pk):
    site=site_access(request,site_code,['staff','coach','manager','admin'])
    event=get_object_or_404(Kaizen,site=site,pk=pk)
    require_event_editor(request.user,event)
    action=get_object_or_404(event.actions,pk=action_pk)
    form=ActionForm(request.POST,event=event,instance=action,auto_id=f'id_action_{action.pk}_%s')
    if form.is_valid():
        with transaction.atomic():
            event=Kaizen.objects.select_for_update().get(pk=event.pk)
            if request.POST.get('event_revision')!=str(event.revision): form.add_error(None,'Another edit was saved. Reload before editing this action.')
            else:
                checkpoint(event,request.user,'Before action edit')
                form.save();reopen_after_change(event);event.revision+=1;event.save()
                checkpoint(event,request.user,'Action updated');log(site,request.user,'kaizen_action_updated',action)
                from django.urls import reverse
                stage=request.POST.get('workspace_stage','Do')
                return redirect(reverse('kaizen_detail',args=[site.code,event.pk])+'?stage='+(stage if stage in ('Plan','Do','Check','Act') else 'Do'))
    return render_kaizen(request,site,event,KaizenStageForm(initial={**event.data,'revision':event.revision}),{'edit_action_id':action.pk,'edit_action_form':form})

@login_required
@require_POST
def kaizen_add(request,site_code,pk,kind):
    allowed=['manager','admin'] if kind=='benefit' else ['coach','manager','admin'] if kind=='participant' else ['staff','coach','manager','admin']
    site=site_access(request,site_code,allowed)
    event=get_object_or_404(Kaizen,site=site,pk=pk)
    forms={'action':ActionForm,'observation':ObservationForm,'benefit':BenefitForm,'participant':ParticipantForm,'document':DocumentUpdateForm,'member':TeamMemberForm}
    if kind not in forms: raise Http404
    if kind=='member':
        if not can_manage_team(request.user,event): raise Http404
    else: require_event_editor(request.user,event)
    form=forms[kind](request.POST,auto_id=f'id_{kind}_%s',**({'event':event} if kind in ('action','member') else {}))
    if form.is_valid():
        with transaction.atomic():
            event=Kaizen.objects.select_for_update().get(pk=event.pk)
            if request.POST.get('event_revision')!=str(event.revision):
                form.add_error(None,'Another edit was saved. Reload before adding this record.')
                return render_kaizen(request,site,event,KaizenStageForm(initial={**event.data,'revision':event.revision}),{kind+'_form':form})
            checkpoint(event,request.user,'Before '+kind+' record')
            if kind=='member':
                user=form.cleaned_data['user']
                # Membership was checked by the form queryset; re-check to block a forged identifier.
                if not Membership.objects.filter(user=user,site=site).exists(): raise Http404
                obj=Participant.objects.create(event=event,user=user,first_initial=(user.first_name[:1] or user.username[:1]).upper(),
                                               last_name=user.last_name or user.username,kaizen_role=form.cleaned_data['kaizen_role'])
            else:
                obj=form.save(commit=False);obj.event=event;obj.save()
            if kind=='observation': reuse_observations(event)
            reopen_after_change(event);event.revision+=1;event.save();checkpoint(event,request.user,kind.title()+' added')
            log(site,request.user,f'kaizen_{kind}_added',obj)
        messages.success(request,{'member':'Team member added. They can now see and edit this event.','action':'Task saved. It shows in the table, the Gantt and the owner\'s task list.'}.get(kind,f'{kind.title()} saved in the full archive.'))
    else:
        messages.error(request,'Could not save the item. Correct the highlighted fields; your entries are retained.')
        return render_kaizen(request,site,event,KaizenStageForm(initial={**event.data,'revision':event.revision}),{kind+'_form':form})
    stage=request.POST.get('workspace_stage')
    url=reverse('kaizen_detail',args=[site.code,event.pk])
    query='?stage='+stage if stage in ('Plan','Do','Check','Act') else ''
    if request.POST.get('actions_view')=='gantt': query+=('&' if query else '?')+'view=gantt'
    return redirect(url+query)

@login_required
def kaizen_template_details(request,site_code,pk):
    site=site_access(request,site_code,['staff','coach','manager','admin'])
    event=get_object_or_404(Kaizen,site=site,pk=pk)
    if request.method=='POST':
        require_event_editor(request.user,event)
        form=KaizenTemplateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                event=Kaizen.objects.select_for_update().get(pk=event.pk)
                if event.revision != form.cleaned_data['revision']:
                    form.add_error(None,'Another edit was saved. Reload and review the latest fields.')
                else:
                    checkpoint(event,request.user,'Before supplementary detail edit')
                    event.data={**event.data,**{k:v for k,v in form.cleaned_data.items() if k!='revision'}}
                    reopen_after_change(event)
                    event.revision+=1;event.save();log(site,request.user,'template_details_saved',event)
                    checkpoint(event,request.user,'Supplementary details saved')
                    messages.success(request,'Source template details saved without truncation.')
                    return redirect('kaizen_template_details',site_code=site.code,pk=event.pk)
    else: form=KaizenTemplateForm(initial={**event.data,'revision':event.revision})
    groups=[('Event / location and team',[11,14,19,20,21,22,23,24,28,29,30,31,33,35]),('Plan: symptoms, process and source taxonomies',[38,40,41,43,47,48,49,50,51,52,54,57]),('Do: solution and contribution',[60,61,62,64]),('Check: result and green impact',[66,75])]
    return render(request,'kaizen_template_details.html',{'site':site,'event':event,'form':form,
        'field_groups':[(name,[form[f'coach_{r}'] for r in rows]) for name,rows in groups]+[('5W2H',[f for f in form.visible_fields() if f.name.startswith('fivew2h_')])],
        'source_lists':form.source_lists})

@login_required
@require_POST
def validate_benefit(request,site_code,pk):
    site=site_access(request,site_code,['manager','admin'])
    obj=get_object_or_404(Benefit,event__site=site,pk=pk)
    with transaction.atomic():
        event=Kaizen.objects.select_for_update().get(pk=obj.event_id)
        checkpoint(event,request.user,'Before benefit validation')
        obj.validated=True;obj.validated_by=request.user;obj.save(update_fields=['validated','validated_by'])
        reopen_after_change(event);event.revision+=1;event.save();checkpoint(event,request.user,'Benefit validated')
    log(site,request.user,'benefit_validated',obj)
    return redirect('kaizen_detail',site_code=site.code,pk=obj.event_id)

@login_required
def evidence(request,site_code):
    site=site_access(request,site_code)
    form=EvidenceForm(request.POST or None,request.FILES or None)
    if request.method=='POST':
        site_access(request,site_code,['assessor','coach','manager','admin'])
        if form.is_valid():
            code=request.POST.get('requirement_code','').strip();ordinal=request.POST.get('clause_ordinal','').strip()
            clause=None
            if code or ordinal:
                clause=Clause.objects.filter(requirement_id=code,ordinal=int(ordinal)).first() if ordinal.isdigit() else None
                if not clause: form.add_error(None,'Select a valid requirement ID and clause number or leave both blank.')
        if form.is_valid():
            obj=form.save(commit=False);obj.site=site;obj.created_by=request.user;obj.save()
            if clause: Coverage.objects.create(evidence=obj,clause=clause,accepted=False)
            log(site,request.user,'evidence_created',obj)
            messages.success(request,'Evidence saved. Clause coverage awaits assessor acceptance.')
            return redirect('evidence',site_code=site.code)
    items=Evidence.objects.filter(site=site).order_by('-created_at')
    if not Membership.objects.filter(user=request.user,site=site,role__in=['manager','admin','assessor']).exists(): items=items.filter(classification='internal')
    requested=request.GET.get('requirement','')
    if requested and not Requirement.objects.filter(code=requested).exists():requested=''
    return render(request,'evidence.html',{'site':site,'items':items,'form':form,'requested_requirement':requested})

@login_required
def other_audit(request,site_code,pk):
    site=site_access(request,site_code,['assessor','manager','admin'])
    item=get_object_or_404(Evidence,site=site,pk=pk,evidence_type='audit')
    existing=OtherAudit.objects.filter(evidence=item).first()
    form=OtherAuditForm(request.POST or None,instance=existing)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False);obj.evidence=item;obj.save()
        log(site,request.user,'other_audit_saved',obj)
        messages.success(request,'Other audit scope saved. No TCA requirement was marked Yes.')
        return redirect('evidence',site_code=site.code)
    return render(request,'other_audit.html',{'site':site,'item':item,'form':form})

@login_required
@require_POST
def link_evidence(request,site_code,pk):
    site=site_access(request,site_code,['assessor','manager','admin'])
    item=get_object_or_404(Evidence,site=site,pk=pk)
    code=request.POST.get('requirement_code','').strip()
    ordinal=request.POST.get('clause_ordinal','').strip()
    clause=Clause.objects.filter(requirement_id=code,ordinal=int(ordinal)).first() if ordinal.isdigit() else None
    if not clause: return HttpResponseForbidden('Choose an existing requirement and clause number.')
    Coverage.objects.get_or_create(evidence=item,clause=clause)
    log(site,request.user,'evidence_linked',item,{'clause':clause.pk})
    messages.success(request,'Clause link added as pending; an assessor must review it.')
    return redirect('evidence',site_code=site.code)

@login_required
def preparation(request,site_code):
    site=site_access(request,site_code)
    if request.method=='POST':
        selected=request.session.get('preparation_selected',{})
        if request.POST.get('selection_action')=='clear':selected[site.code]=[]
        elif request.POST.get('selection_action')=='add':
            submitted=set(request.POST.getlist('selected'))
            allowed=set(Requirement.objects.filter(code__in=submitted).values_list('code',flat=True))
            selected[site.code]=sorted(set(selected.get(site.code,[]))|allowed)
        request.session['preparation_selected']=selected
        messages.success(request,f"{len(selected.get(site.code,[]))} requirements in the export selection.")
        target=redirect('preparation',site_code=site.code)
        if request.POST.get('page','').isdigit():target['Location']+=f"?page={int(request.POST['page'])}"
        return target
    saved=request.session.get('preparation_filters',{})
    if request.GET.get('clear'):
        saved.pop(site.code,None);request.session['preparation_filters']=saved
        return redirect('preparation',site_code=site.code)
    filter_keys=('category','level','evidence_type','owner','due')
    parameters=request.GET if any(key in request.GET for key in filter_keys) else saved.get(site.code,{})
    filter_form=PreparationFilterForm(parameters)
    valid=filter_form.is_valid()
    filters=filter_form.cleaned_data if valid else {}
    if valid:
        saved[site.code]={key:str(value) for key,value in filters.items() if value is not None}
        request.session['preparation_filters']=saved
    from .preparation_service import preparation_items
    items=preparation_items(site,filters) if valid else []
    if request.GET.get('format')=='csv' and valid:
        import csv
        response=HttpResponse(content_type='text/csv')
        response['Content-Disposition']='attachment; filename="evidence-preparation.csv"'
        writer=csv.writer(response)
        writer.writerow(['Requirement ID','Category','Level','Official detail','Expected evidence','Response','Accepted evidence records','Action type','Owner','Due date'])
        for row in items:
            r=row['requirement'];writer.writerow([r.code,r.category.name,r.level_code,r.detail_text,r.expected_evidence,row['response'],row['accepted'],row['action_type'],row['owner'],row['due_date'] or ''])
        return response
    active_filters=[(filter_form[key].label,dict(filter_form.fields[key].choices).get(value,value) if hasattr(filter_form.fields[key],'choices') else value)
                    for key,value in filters.items() if value]
    page=Paginator(items,25).get_page(request.GET.get('page'))
    selected=request.session.get('preparation_selected',{}).get(site.code,[])
    for item in page.object_list:item['is_selected']=item['requirement'].code in selected
    return render(request,'preparation.html',{'site':site,'items':items,'visible_items':page.object_list,'page':page,
        'selected_count':len(selected),'filter_form':filter_form,'active_filters':active_filters,
        'filter_query':request.GET.urlencode()})

@login_required
@require_POST
def review_coverage(request,site_code,pk):
    site=site_access(request,site_code,['assessor','manager','admin'])
    coverage=get_object_or_404(Coverage.objects.select_related('evidence','clause'),pk=pk,evidence__site=site)
    decision=request.POST.get('decision','')
    if decision not in ('accept','reject'): return HttpResponseForbidden('Choose accept or reject.')
    reason=request.POST.get('reason','').strip()
    if not reason: return HttpResponseForbidden('An assessor decision reason is required.')
    if decision=='accept' and coverage.evidence.valid_until and coverage.evidence.valid_until<timezone.localdate():
        return HttpResponseForbidden('Expired evidence cannot be accepted for current reuse.')
    if decision=='accept' and coverage.evidence.evidence_type=='audit' and not OtherAudit.objects.filter(evidence=coverage.evidence).exists():
        return HttpResponseForbidden('Record audit scope, period, tested control, and finding before accepting coverage.')
    coverage.accepted=decision=='accept';coverage.decision=reason;coverage.reviewed_by=request.user;coverage.reviewed_at=timezone.now();coverage.save()
    log(site,request.user,'coverage_reviewed',coverage,{'accepted':coverage.accepted})
    messages.success(request,'Clause coverage decision saved. Requirement response remains separate.')
    return redirect('evidence',site_code=site.code)

@login_required
def download(request,site_code,pk):
    site=site_access(request,site_code)
    item=get_object_or_404(Evidence,site=site,pk=pk)
    if item.classification!='internal' and not Membership.objects.filter(user=request.user,site=site,role__in=['manager','admin','assessor']).exists(): raise Http404
    if not item.file: raise Http404
    from .storage import open_or_404
    return FileResponse(open_or_404(item.file),as_attachment=True,filename=item.file.name.split('/')[-1])

@login_required
def report(request,site_code):
    from .progress import coverage_progress,progress_export
    site=site_access(request,site_code);latest=site.assessments.first()
    approved=site.assessments.filter(status='approved').first()
    data={'site':site.name,'policy':latest.policy_version if latest else None,'approved_policy':False,'assessment':None,'dated_snapshot':approved.snapshot if approved else None,'categories':[]}
    data['verified_progress']=progress_export(coverage_progress(site))
    if latest:
        data['assessment']={'version':latest.version,'status':latest.status,'approved_at':latest.approved_at.isoformat() if latest.approved_at else None}
        codes,unverified=accepted_codes(site,latest)
        data['unverified_yes']=unverified
        for cat in Category.objects.all(): data['categories'].append({'name':cat.name,'result':category_result({r.position:codes.get(r.code,'') for r in cat.requirements.all()},latest.policy_version)})
    return JsonResponse(data,json_dumps_params={'indent':2})

@login_required
def assessment_archive(request,site_code):
    site=site_access(request,site_code)
    obj=site.assessments.first()
    responses={r.requirement_id:r for r in obj.responses.all()} if obj else {}
    codes,unverified=accepted_codes(site,obj)
    rows=[]
    for req in Requirement.objects.select_related('category','source_version').prefetch_related('clauses'):
        response=responses.get(req.code)
        rows.append({'id':req.code,'category':req.category.name,'level_code':req.level_code,
                     'official_details':req.detail_text,'reasoning':req.reasoning,'expected_evidence':req.expected_evidence,
                     'remote_method':req.remote_method,'source_address':req.source_address,
                     'source_sha256':req.source_version.sha256,
                     'clauses':[{'address':c.source_address,'exact_text':c.exact_text} for c in req.clauses.all()],
                     'response':response.code if response else '',
                     'conclusion':response.conclusion if response else '',
                     'advisory_follow_up':response.advisory_follow_up if response else '',
                     'advisory_retest_status':response.advisory_retest_status if response else '',
                     'frozen_site_question':question_for_assessment(obj,req),
                     'accepted_for_readiness':codes.get(req.code) in pass_codes(obj.policy_version if obj else 'draft-v1')})
    return JsonResponse({'site':site.name,'assessment_version':obj.version if obj else None,
                         'status':obj.status if obj else None,'policy':obj.policy_version if obj else None,'approved_policy':False,
                         'unverified_yes':unverified,'requirements':rows},json_dumps_params={'indent':2})

@login_required
def kaizen_archive(request,site_code,pk):
    site=site_access(request,site_code);obj=get_object_or_404(Kaizen,site=site,pk=pk)
    financial_access=Membership.objects.filter(user=request.user,site=site,role__in=['assessor','manager','admin']).exists()
    participant_access=Membership.objects.filter(user=request.user,site=site,role__in=['assessor','coach','manager','admin']).exists()
    data=public_snapshot(snapshot(obj),financial_access,participant_access)
    data['source_field_mapping']='core/forms.py and docs/KAIZEN_FIELD_RULES.md'
    data['revision']=obj.revision
    data['history']=[{'revision':r.revision,'state':r.state,'reason':r.reason,'at':r.created_at.isoformat(),
                      'snapshot':public_snapshot(r.snapshot,financial_access,participant_access)} for r in obj.history.all()]
    return JsonResponse(data,json_dumps_params={'indent':2})

@login_required
def kaizen_excel(request,site_code,pk):
    site=site_access(request,site_code);obj=get_object_or_404(Kaizen,site=site,pk=pk)
    errors=export_errors(obj)
    if errors: return JsonResponse({'export_errors':errors},status=422)
    financial_access=Membership.objects.filter(user=request.user,site=site,role__in=['assessor','manager','admin']).exists()
    participant_access=Membership.objects.filter(user=request.user,site=site,role__in=['assessor','coach','manager','admin']).exists()
    output=archive_xlsx(obj,financial_access,participant_access,request.user)
    response=HttpResponse(output.getvalue(),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition']=f'attachment; filename="kaizen-{obj.pk}-archive.xlsx"'
    return response
