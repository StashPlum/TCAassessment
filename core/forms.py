from django import forms
from .models import AssessmentSession, Benefit, DocumentUpdate, Evidence, Kaizen, KaizenAction, Observation, Opportunity, OtherAudit, Participant, Requirement
from .source import coach_labels, document_types, star_criteria

class ResponseForm(forms.Form):
    code = forms.ChoiceField(choices=[('', 'Unanswered'), ('Y','Yes'), ('N','No'), ('A','A — Advisory pass with follow-up')], required=False)
    conclusion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    advisory_follow_up = forms.CharField(widget=forms.Textarea(attrs={'rows':2}),required=False,label='Advisory improvement and follow-up')
    retest_confirm = forms.BooleanField(required=False,label='I explicitly retested the previous Advisory in this assessment')
    revision = forms.IntegerField(widget=forms.HiddenInput)

class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = ['title','evidence_type','owner','version','period_start','period_end','valid_until','classification','source','file']
        widgets = {**{k: forms.DateInput(attrs={'type':'date'}) for k in ['period_start','period_end','valid_until']},'source':forms.Textarea(attrs={'rows':3})}
    def clean_file(self):
        file=self.cleaned_data.get('file')
        if file and file.size>10*1024*1024:
            raise forms.ValidationError('Files over 10 MB are not accepted in the local pilot.')
        return file

class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ['requirement','kind','problem','proposed_measure','owner','due_date','immediate_corrective','prerequisite','priority_override']
        widgets = {'due_date': forms.DateInput(attrs={'type':'date'}),'problem':forms.Textarea(attrs={'rows':3}),'proposed_measure':forms.Textarea(attrs={'rows':2})}

class SessionForm(forms.ModelForm):
    blocks_text=forms.CharField(label='Time blocks',required=False,widget=forms.Textarea(attrs={'rows':3}),
        help_text='One per line: 09:00-09:45 | 2 people | Safety and operations')
    class Meta:
        model = AssessmentSession
        fields = ['date','purpose','scope_text','method','participants','blocks_text','notes','owner','requirements']
        widgets = {'date': forms.DateInput(attrs={'type':'date'}), 'requirements':forms.SelectMultiple(attrs={'size':8}),
                   'notes':forms.Textarea(attrs={'rows':3}),'purpose':forms.Textarea(attrs={'rows':2}),
                   'scope_text':forms.Textarea(attrs={'rows':2}),'participants':forms.Textarea(attrs={'rows':2})}
    def clean_blocks_text(self):
        rows=[]
        for number,line in enumerate(self.cleaned_data['blocks_text'].splitlines(),1):
            if not line.strip(): continue
            parts=[part.strip() for part in line.split('|')]
            if len(parts)!=3 or '-' not in parts[0]:
                raise forms.ValidationError(f'Line {number}: use HH:MM-HH:MM | people | role.')
            start,end=[value.strip() for value in parts[0].split('-',1)]
            from datetime import time
            try:
                start=time.fromisoformat(start);end=time.fromisoformat(end)
                people=int(parts[1])
            except ValueError:
                raise forms.ValidationError(f'Line {number}: enter valid times and a whole number of people.')
            if end<=start or people<1 or people>100 or not parts[2]:
                raise forms.ValidationError(f'Line {number}: end after start, 1–100 people and a role are required.')
            rows.append({'start':start.strftime('%H:%M'),'end':end.strftime('%H:%M'),'people':people,'role':parts[2]})
        return rows
    def clean(self):
        data=super().clean()
        if 'remote' in (data.get('method') or '').lower():
            blocked=[r.code for r in data.get('requirements',[]) if 'remote assessment not applicable' in r.remote_method.lower()]
            if blocked: raise forms.ValidationError('Source does not permit remote assessment for '+', '.join(blocked))
        return data

class SessionChangeForm(SessionForm):
    change_reason=forms.CharField(label='Reason for change',widget=forms.Textarea(attrs={'rows':2}))
    impact=forms.CharField(label='Operational impact',widget=forms.Textarea(attrs={'rows':2}))
    followup_owner=forms.CharField(label='Follow-up owner',max_length=160)
    revision=forms.IntegerField(widget=forms.HiddenInput)

class SessionReviewForm(forms.Form):
    availability=forms.ChoiceField(choices=[('confirmed','Confirm availability'),('alternative','Suggest an alternative'),('blocked','Record blocker')])
    alternate_date=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
    backup_participants=forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':2}),label='Alternative or backup people')
    manager_note=forms.CharField(widget=forms.Textarea(attrs={'rows':2}),label='Availability note / blocker')
    revision=forms.IntegerField(widget=forms.HiddenInput)
    def clean(self):
        data=super().clean()
        if data.get('availability')=='alternative' and not (data.get('alternate_date') or data.get('backup_participants')):
            self.add_error('alternate_date','Propose a new date or backup participants.')
        return data

class PreparationNeedForm(forms.Form):
    evidence_items=forms.CharField(label='Site documentation needs',widget=forms.Textarea(attrs={'rows':5}),
        help_text='One item per line. Official clauses remain unchanged.')
    owner=forms.CharField(max_length=160,required=False,label='Document owner')
    period_start=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
    period_end=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
    source_note=forms.CharField(label='Source / provenance',widget=forms.Textarea(attrs={'rows':2}))
    change_reason=forms.CharField(label='Reason for change',widget=forms.Textarea(attrs={'rows':2}))
    expected_version=forms.IntegerField(widget=forms.HiddenInput,min_value=0)
    def clean(self):
        data=super().clean()
        if data.get('period_start') and data.get('period_end') and data['period_end']<data['period_start']:
            self.add_error('period_end','End must be on or after start.')
        return data

class OtherAuditForm(forms.ModelForm):
    class Meta:
        model = OtherAudit
        fields = ['scope','period_start','period_end','tested_control','finding']
        widgets = {**{k:forms.DateInput(attrs={'type':'date'}) for k in ['period_start','period_end']},**{k:forms.Textarea(attrs={'rows':3}) for k in ['scope','tested_control','finding']}}
    def clean(self):
        data=super().clean()
        if data.get('period_start') and data.get('period_end') and data['period_end']<data['period_start']:
            raise forms.ValidationError('Audit period end must be on or after its start.')
        return data

HELP_SCOPE=[('one','One step'),('several','Several steps'),('site','Site-wide')]
HELP_RECURRENCE=[('once','One-off'),('recurring','Recurring')]
HELP_CAUSE=[('known','Known'),('partly','Partly'),('unknown','Unknown')]

class KaizenForm(forms.ModelForm):
    cross_process = forms.BooleanField(required=False,label='Several processes / departments')
    unknown_cause = forms.BooleanField(required=False,label='Cause still unknown')
    recurring = forms.BooleanField(required=False,label='Recurring problem')
    help_scope = forms.ChoiceField(required=False,choices=HELP_SCOPE,widget=forms.RadioSelect,label='Process scope')
    help_recurrence = forms.ChoiceField(required=False,choices=HELP_RECURRENCE,widget=forms.RadioSelect,label='Does the problem recur?')
    help_cause = forms.ChoiceField(required=False,choices=HELP_CAUSE,widget=forms.RadioSelect,label='Is the cause known?')
    owner = forms.CharField(max_length=160, required=False)
    process_location = forms.CharField(max_length=200, required=False, label='Process / location')
    due_date = forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
    specific_problem = forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':2}),label='Specific problem',
        help_text='Optional now; needed before Plan moves to Do.')
    requirement = forms.CharField(required=False,max_length=15,widget=forms.HiddenInput)
    class Meta:
        model = Kaizen
        fields = ['title','input_profile','profile','opportunity']
        labels={'title':'Title','profile':'Methodological type','opportunity':'Linked finding','input_profile':'Input view'}
        widgets={'input_profile':forms.RadioSelect,'title':forms.TextInput(attrs={'maxlength':200,'data-counter':'75'})}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['title'].help_text='Also becomes the overall problem. The Excel template allows 75 characters.'
        self.fields['profile'].required=False
        self.fields['profile'].initial='A4'
        self.fields['profile'].choices=[c for c in self.fields['profile'].choices if c[0]]
        self.fields['profile'].help_text='A4 by default. Separate from the input view and the report paper.'
        self.fields['input_profile'].choices=[c for c in self.fields['input_profile'].choices if c[0] not in ('legacy','')]
        self.fields['input_profile'].initial=None
        self.fields['input_profile'].required=False
    def clean_profile(self): return self.cleaned_data.get('profile') or 'A4'
    def suggestion(self):
        from .profiles import suggest_profile
        data=self.data
        cross=bool(data.get('cross_process')) or data.get('help_scope') in ('several','site')
        unknown=bool(data.get('unknown_cause')) or data.get('help_cause') in ('partly','unknown')
        recurring=bool(data.get('recurring')) or data.get('help_recurrence')=='recurring'
        return suggest_profile(cross,unknown,recurring)
    def clean_input_profile(self):
        return self.cleaned_data.get('input_profile') or self.suggestion()[0]
    def clean_requirement(self):
        code=self.cleaned_data.get('requirement','').strip()
        if code and not Requirement.objects.filter(code=code).exists(): raise forms.ValidationError('Choose an existing TCA requirement.')
        return code

class KaizenStageForm(forms.Form):
    outcome_criterion = forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':2}),label='Desired outcome / observable check criterion')
    observed_result = forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':2}),label='Actual result and evidence conclusion')
    result_date = forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
    owner = forms.CharField(max_length=160,required=False)
    process_location = forms.CharField(max_length=200,required=False,label='Process / location')
    due_date = forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
    cause_status = forms.ChoiceField(choices=[('','Not recorded'),('hypothesis','Cause hypothesis'),('supported','Cause supported by investigation')],required=False)
    sustain_owner = forms.CharField(max_length=160,required=False)
    sustain_check = forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':2}),label='Sustain check / learning')
    overall_problem = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False, label='Overall problem (PLAN!B11)')
    specific_problem = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False, label='Specific problem (PLAN!B63)')
    root_cause = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False, label='Investigated root cause (PLAN!B85)')
    measure = forms.CharField(required=False, label='Local measure (PLAN!B24)')
    baseline = forms.DecimalField(required=False, label='Before average (PLAN!B27)')
    target = forms.DecimalField(required=False, label='Target (PLAN!B30)')
    unit = forms.CharField(required=False, label='Measure unit')
    population = forms.CharField(required=False, label='Measured population')
    direction = forms.ChoiceField(choices=[('', 'Choose'), ('up','Higher is better'), ('down','Lower is better')], required=False)
    solution = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False, label='Countermeasure (DO!B15)')
    actual = forms.DecimalField(required=False, label='After average (CHECK!B26)')
    result_period_start = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))
    result_period_end = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))
    data_points = forms.IntegerField(required=False, min_value=0)
    data_source = forms.CharField(required=False)
    sustain = forms.CharField(widget=forms.Textarea(attrs={'rows':3}), required=False, label='Sustain plan (ACT)')
    document_types = forms.CharField(required=False, help_text='Different updated document or site-tool types, separated by commas')
    coach_review = forms.CharField(widget=forms.Textarea(attrs={'rows':2}), required=False,label='Sensei review')
    next_kaizen_action = forms.CharField(widget=forms.Textarea(attrs={'rows':2}), required=False, label='Follow-up action if target unmet (ACT)')
    revision = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for number,text,address in star_criteria():
            self.fields[f'star_{number}']=forms.ChoiceField(choices=[('', 'Not reviewed'),('Y','Yes'),('N','No')],
                required=False,label=f'Star {number} review ({address})',help_text=text)
        for field in self.fields.values():
            if field.label: field.label=field.label.split(' (')[0]
    def clean(self):
        data=super().clean()
        if data.get('result_period_start') and data.get('result_period_end') and data['result_period_end']<data['result_period_start']:
            self.add_error('result_period_end','End date must be on or after the start date.')
        return data

class PreparationFilterForm(forms.Form):
    category=forms.ChoiceField(required=False,label='Category')
    level=forms.ChoiceField(required=False,choices=[('','All levels'),('C','Certified'),('B','Advanced'),('A','Showcase')])
    evidence_type=forms.ChoiceField(required=False,choices=[('','All types'),('document','Document'),('observation','Observation'),('interview','Interview'),('audit','Other audit')])
    owner=forms.CharField(required=False,max_length=160)
    due=forms.DateField(required=False,label='Due by',widget=forms.DateInput(attrs={'type':'date'}))
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        from .models import Category
        self.fields['category'].choices=[('','All categories')]+[(str(c.number),str(c)) for c in Category.objects.all()]

class ReviewNoteForm(forms.Form):
    stage=forms.ChoiceField(choices=[(s,s) for s in ('Plan','Do','Check','Act')])
    kind=forms.ChoiceField(choices=[('advice','Advice'),('clarify','Request clarification'),('return','Return for changes')])
    text=forms.CharField(widget=forms.Textarea(attrs={'rows':3}),label='Advice or specific request',max_length=10000)
    revision=forms.IntegerField(widget=forms.HiddenInput)

REVIEW_STATES=[('submitted','Submitted'),('returned','Sensei feedback'),('in_progress','In progress'),('finalised','Finalised'),('all','All')]

class ReviewQueueForm(forms.Form):
    state=forms.ChoiceField(required=False,choices=REVIEW_STATES,label='Review status')
    scope=forms.ChoiceField(required=False,choices=[('submitted','Submitted for review'),('all','All active work')])
    stage=forms.ChoiceField(required=False,choices=[('','All stages')]+[(s,s) for s in ('Plan','Do','Check','Act')])
    due=forms.DateField(required=False,label='Due by',widget=forms.DateInput(attrs={'type':'date'}))
    readiness=forms.ChoiceField(required=False,choices=[('','All readiness'),('ready','Ready for local verification'),('missing','Needs attention')])
    q=forms.CharField(required=False,max_length=200,label='Search')

class ActionForm(forms.ModelForm):
    """Actions and tasks are one record type; the owner comes from the team when an assignee is chosen."""
    class Meta:
        model = KaizenAction
        fields = ['phase','description','assignee','owner','start_date','end_date','progress','key_action']
        widgets = {**{k: forms.DateInput(attrs={'type':'date'}) for k in ['start_date','end_date']},'description':forms.Textarea(attrs={'rows':2})}
        labels = {'assignee':'Owner from team','owner':'Other owner (not on the team)','progress':'Progress %'}
    def __init__(self,*args,event=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['owner'].required=False
        self.fields['progress'].required=False
        self.fields['progress'].widget=forms.Select(choices=[(v,str(v)+'%') for v in (0,20,40,60,80,100)])
        team=event.participants.select_related('user') if event is not None else Participant.objects.none()
        self.fields['assignee'].queryset=team
        from .kaizen import team_display
        self.fields['assignee'].label_from_instance=lambda p: team_display(p)+' · '+p.kaizen_role
        self.fields['assignee'].empty_label='Choose a team member'
    def clean_progress(self):
        value=self.cleaned_data.get('progress')
        if value in (None,''): return 0
        if value>100: raise forms.ValidationError('Progress is 0 to 100%.')
        return value
    def clean(self):
        data=super().clean()
        if data.get('start_date') and data.get('end_date') and data['end_date']<data['start_date']:
            raise forms.ValidationError('End date must be on or after start date.')
        if data.get('assignee'):
            from .kaizen import team_display
            data['owner']=team_display(data['assignee'])
            self.instance.owner=data['owner']
        elif not (data.get('owner') or '').strip():
            self.add_error('assignee','Choose an owner from the team or name another owner.')
        return data

class TeamMemberForm(forms.Form):
    """Adds an authorized site user to one event; contact details are not copied."""
    user=forms.ModelChoiceField(queryset=None,label='Site member',empty_label='Choose a site member')
    kaizen_role=forms.ChoiceField(choices=[('Kaizen lead','Kaizen lead'),('Team member','Team member'),('Subject expert','Subject expert'),('Sensei','Sensei')],label='Role in this event',initial='Team member')
    def __init__(self,*args,event=None,**kwargs):
        super().__init__(*args,**kwargs)
        from django.contrib.auth import get_user_model
        users=get_user_model().objects.filter(membership__site=event.site).distinct().order_by('username') if event else get_user_model().objects.none()
        if event: users=users.exclude(pk__in=event.participants.filter(user__isnull=False).values_list('user_id',flat=True))
        self.fields['user'].queryset=users
        self.fields['user'].label_from_instance=lambda u: u.get_full_name() or u.username

PHASES=('Plan','Do','Check','Act')

class ReviewDecisionForm(forms.Form):
    """Sensei feedback per PDCA phase; returning needs at least one comment."""
    feedback_Plan=forms.CharField(required=False,max_length=10000,widget=forms.Textarea(attrs={'rows':2}),label='Plan')
    feedback_Do=forms.CharField(required=False,max_length=10000,widget=forms.Textarea(attrs={'rows':2}),label='Do')
    feedback_Check=forms.CharField(required=False,max_length=10000,widget=forms.Textarea(attrs={'rows':2}),label='Check')
    feedback_Act=forms.CharField(required=False,max_length=10000,widget=forms.Textarea(attrs={'rows':2}),label='Act')
    coach_review=forms.CharField(required=False,max_length=32767,widget=forms.Textarea(attrs={'rows':3}),label='Overall sensei review')
    decision=forms.ChoiceField(choices=[('return','Return with feedback'),('finalize','Finalise and create A3')])
    revision=forms.IntegerField(widget=forms.HiddenInput)
    def comments(self):
        return [(phase,self.cleaned_data['feedback_'+phase].strip()) for phase in PHASES if self.cleaned_data.get('feedback_'+phase,'').strip()]
    def clean(self):
        data=super().clean()
        if data.get('decision')=='return' and not self.comments():
            raise forms.ValidationError('Write at least one comment before returning the event.')
        return data

class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ['phase','measure','value','unit','population','period_start','period_end','data_source']
        widgets = {**{k: forms.DateInput(attrs={'type':'date'}) for k in ['period_start','period_end']},'data_source':forms.Textarea(attrs={'rows':2})}
    def clean(self):
        data=super().clean()
        if data.get('period_start') and data.get('period_end') and data['period_end']<data['period_start']:
            raise forms.ValidationError('Period end must be on or after period start.')
        return data

class BenefitForm(forms.ModelForm):
    class Meta:
        model = Benefit
        fields = ['kind','amount','unit','period_start','period_end']
        widgets = {k: forms.DateInput(attrs={'type':'date'}) for k in ['period_start','period_end']}

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['first_initial','last_name','email','role_profile','kaizen_role','estimated_hours']

class DocumentUpdateForm(forms.ModelForm):
    class Meta:
        model = DocumentUpdate
        fields = ['document_type','document_number','name','updated_at']
        widgets = {'updated_at':forms.DateInput(attrs={'type':'date'})}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['document_type']=forms.ChoiceField(choices=[('', 'Choose source document type')]+document_types())

EXTRA_ROWS=(11,14,19,20,21,22,23,24,28,29,30,31,33,35,38,40,41,43,47,48,49,50,51,52,54,57,60,61,62,64,66,75)
class KaizenTemplateForm(forms.Form):
    revision=forms.IntegerField(widget=forms.HiddenInput)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for row,label in coach_labels(EXTRA_ROWS):
            self.fields[f'coach_{row}']=forms.CharField(required=False,label=f'{label} (COACH REVIEW!B{row})',max_length=32767)
        from .source import source_taxonomies
        taxonomies=source_taxonomies()
        mapping={47:'KPI',54:'Gen_Problem',57:'Gen_RC',62:'GENERIC_SOLUTION'}
        self.source_lists=[]
        for row,name in mapping.items():
            if name in taxonomies:
                self.fields[f'coach_{row}'].widget.attrs['list']='taxonomy-'+name
                self.fields[f'coach_{row}'].help_text='Original template list suggestions; legacy values retained. Reference freshness and official submission rules require owner confirmation.'
                self.source_lists.append((name,taxonomies[name]))
        for key,label in [('why','Why'),('where','Where'),('who','Who'),('what','What'),('when','When'),('how','How'),('how_many','How many')]:
            self.fields[f'fivew2h_{key}']=forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':2}),label=f'5W2H {label}')
