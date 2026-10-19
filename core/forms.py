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
    class Meta:
        model = AssessmentSession
        fields = ['date','method','notes','owner','requirements']
        widgets = {'date': forms.DateInput(attrs={'type':'date'}), 'requirements':forms.SelectMultiple(attrs={'size':8}), 'notes':forms.Textarea(attrs={'rows':3})}
    def clean(self):
        data=super().clean()
        if 'remote' in (data.get('method') or '').lower():
            blocked=[r.code for r in data.get('requirements',[]) if 'remote assessment not applicable' in r.remote_method.lower()]
            if blocked: raise forms.ValidationError('Source does not permit remote assessment for '+', '.join(blocked))
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

class KaizenForm(forms.ModelForm):
    cross_process = forms.BooleanField(required=False,label='Several processes / departments')
    unknown_cause = forms.BooleanField(required=False,label='Cause still unknown')
    recurring = forms.BooleanField(required=False,label='Recurring problem')
    owner = forms.CharField(max_length=160, required=False)
    process_location = forms.CharField(max_length=200, required=False, label='Process / location')
    due_date = forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
    class Meta:
        model = Kaizen
        fields = ['title','input_profile','profile','opportunity']
        labels={'title':'Problem / working title','profile':'Methodological profile','opportunity':'Linked finding'}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['profile'].required=False
        self.fields['profile'].initial='A4'
        self.fields['input_profile'].choices=[c for c in self.fields['input_profile'].choices if c[0]!='legacy']
        self.fields['input_profile'].initial='small'
        self.fields['input_profile'].required=False
    def clean_profile(self): return self.cleaned_data.get('profile') or 'A4'
    def clean_input_profile(self):
        from .profiles import suggest_profile
        return self.cleaned_data.get('input_profile') or suggest_profile(bool(self.data.get('cross_process')),bool(self.data.get('unknown_cause')),bool(self.data.get('recurring')))[0]

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

class ReviewQueueForm(forms.Form):
    scope=forms.ChoiceField(required=False,choices=[('submitted','Submitted for review'),('all','All active work')])
    stage=forms.ChoiceField(required=False,choices=[('','All stages')]+[(s,s) for s in ('Plan','Do','Check','Act')])
    due=forms.DateField(required=False,label='Due by',widget=forms.DateInput(attrs={'type':'date'}))
    readiness=forms.ChoiceField(required=False,choices=[('','All readiness'),('ready','Ready for local verification'),('missing','Needs attention')])

class ActionForm(forms.ModelForm):
    class Meta:
        model = KaizenAction
        fields = ['phase','description','owner','start_date','end_date','key_action']
        widgets = {**{k: forms.DateInput(attrs={'type':'date'}) for k in ['start_date','end_date']},'description':forms.Textarea(attrs={'rows':3})}
    def clean(self):
        data=super().clean()
        if data.get('start_date') and data.get('end_date') and data['end_date']<data['start_date']:
            raise forms.ValidationError('End date must be on or after start date.')
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
