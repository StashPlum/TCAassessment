from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from .storage import PrivateLocalStorage

class Site(models.Model):
    COUNTRY_CHOICES = [('NL','Netherlands'),('BE','Belgium'),('LU','Luxembourg'),('GB','United Kingdom')]
    name = models.CharField(max_length=180, unique=True)
    code = models.SlugField(unique=True)
    country_code = models.CharField(max_length=2, choices=COUNTRY_CHOICES, blank=True)
    organization = models.CharField(max_length=180, default='CEVA Logistics')
    region = models.CharField(max_length=120, blank=True)
    grouping = models.CharField(max_length=120, blank=True)
    target_level = models.CharField(max_length=1, choices=[('C','Certified'),('B','Advanced'),('A','Showcase')], default='C')
    def __str__(self): return self.name

class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    role = models.CharField(max_length=12, choices=[(x,x.title()) for x in ('staff','assessor','coach','manager','admin')])
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','site','role'], name='unique_site_role')]

class SourceVersion(models.Model):
    filename = models.CharField(max_length=255, unique=True)
    sha256 = models.CharField(max_length=64)
    imported_at = models.DateTimeField(auto_now_add=True)

class Category(models.Model):
    number = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    source_address = models.CharField(max_length=60)
    def __str__(self): return f'{self.number}. {self.name}'

class Requirement(models.Model):
    code = models.CharField(max_length=15, primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='requirements')
    level_code = models.CharField(max_length=1)
    position = models.PositiveSmallIntegerField()
    detail_text = models.TextField()
    reasoning = models.TextField(blank=True)
    expected_evidence = models.TextField(blank=True)
    remote_method = models.TextField(blank=True)
    source_address = models.CharField(max_length=60)
    source_version = models.ForeignKey(SourceVersion, on_delete=models.PROTECT)
    tags = models.CharField(max_length=300, blank=True)
    plain_explanation = models.TextField(blank=True)
    class Meta:
        ordering = ['category_id','position']
        indexes = [models.Index(fields=['category','position'])]
    def __str__(self): return self.code

class Clause(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name='clauses')
    ordinal = models.PositiveSmallIntegerField()
    source_address = models.CharField(max_length=50)
    exact_text = models.TextField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=['requirement','ordinal'], name='unique_clause_ordinal')]
        ordering = ['ordinal']

class Assessment(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='assessments')
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=[('draft','Draft'),('approved','Approved')], default='draft')
    policy_version = models.CharField(max_length=20, default='advisory-v2')
    rationale = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_assessments')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='approved_assessments')
    approved_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=0)
    snapshot = models.JSONField(default=dict)  # frozen accepted coverage and category results at approval
    scope_snapshot = models.JSONField(default=dict)  # explicit frozen denominator; legacy snapshots untouched
    configuration_snapshot = models.JSONField(default=dict)  # frozen local question/evidence wording for this assessment
    preparation_snapshot = models.JSONField(default=dict)  # frozen site documentation needs for this assessment
    planned_session = models.ForeignKey('AssessmentSession', null=True, blank=True, on_delete=models.SET_NULL, related_name='assessments')
    full_section_review = models.BooleanField(default=False)  # targeted decisions never reset section frequency
    def save(self,*args,**kwargs):
        if self._state.adding and not self.scope_snapshot:
            from .progress import baseline_scope
            self.scope_snapshot=baseline_scope()
        if self._state.adding and not self.configuration_snapshot:
            from .assessment_config import frozen_configuration
            self.configuration_snapshot=frozen_configuration(self.site)
        if self._state.adding and not self.preparation_snapshot:
            from .assessment_config import frozen_preparation
            self.preparation_snapshot=frozen_preparation(self.site)
        return super().save(*args,**kwargs)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['site','version'], name='unique_site_assessment_version')]
        ordering = ['-version']

class Response(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='responses')
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT)
    code = models.CharField(max_length=1, choices=[('Y','Yes'),('N','No'),('A','Advisory'),('','Unanswered')], blank=True)
    conclusion = models.TextField(blank=True)
    advisory_follow_up = models.TextField(blank=True)
    advisory_retest_status = models.CharField(max_length=16, default='not_due', choices=[('not_due','Not due'),('due_next','Due at next assessment'),('pending','Pending retest'),('retested','Retested')])
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['assessment','requirement'], name='unique_assessment_requirement')]

class ApplicabilityException(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT)
    justification = models.TextField()
    scope = models.TextField()
    source_authority = models.TextField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    approved_at = models.DateTimeField(null=True, blank=True)

class SiteQuestionVersion(models.Model):
    """Append-only local wording; official source clauses remain in Requirement/Clause."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='question_versions')
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, related_name='site_versions')
    version = models.PositiveIntegerField()
    kind = models.CharField(max_length=20, choices=[('local_guidance','Local guidance'),('official_proposal','Official change proposal')])
    question_text = models.TextField()
    evidence_items = models.JSONField(default=list)
    local_explanation = models.TextField(blank=True)
    change_reason = models.TextField()
    diff = models.JSONField(default=dict)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['site','requirement','version'], name='unique_site_question_version')]
        ordering = ['-version']
    def save(self,*args,**kwargs):
        if not self._state.adding: raise ValueError('Site question versions are immutable; create a new version.')
        return super().save(*args,**kwargs)

class PreparationNeedVersion(models.Model):
    """Append-only site documentation request; never edits the official obligation."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='preparation_versions')
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    evidence_items = models.JSONField(default=list)
    owner = models.CharField(max_length=160, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    source_note = models.TextField()
    change_reason = models.TextField()
    diff = models.JSONField(default=dict)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['site','requirement','version'], name='unique_site_preparation_version')]
        ordering = ['-version']
    def save(self,*args,**kwargs):
        if not self._state.adding: raise ValueError('Preparation versions are immutable; create a new version.')
        return super().save(*args,**kwargs)

class Evidence(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    evidence_type = models.CharField(max_length=30, choices=[('document','Document'),('observation','Observation'),('interview','Interview'),('audit','Other audit')])
    owner = models.CharField(max_length=160)
    version = models.CharField(max_length=80, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    classification = models.CharField(max_length=20, choices=[('internal','Internal'),('hr','HR restricted'),('financial','Financial restricted')], default='internal')
    source = models.TextField(blank=True)
    file = models.FileField(upload_to='evidence/%Y/%m/', storage=PrivateLocalStorage(), null=True, blank=True, validators=[FileExtensionValidator(['pdf','png','jpg','jpeg','xlsx','docx','txt'])])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.title} · {self.version or "version unset"}'

class Coverage(models.Model):
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='coverage')
    clause = models.ForeignKey(Clause, on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)
    decision = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['evidence','clause'], name='unique_evidence_clause')]

class AssessmentSession(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date = models.DateField()
    method = models.CharField(max_length=40)
    notes = models.TextField(blank=True)
    requirements = models.ManyToManyField(Requirement, blank=True)
    owner = models.CharField(max_length=160, blank=True)
    purpose = models.TextField(blank=True)
    scope_text = models.TextField(blank=True)
    participants = models.TextField(blank=True)
    time_blocks = models.JSONField(default=list)
    availability = models.CharField(max_length=16, choices=[('proposed','Awaiting review'),('confirmed','Confirmed'),('alternative','Alternative proposed'),('blocked','Blocker')], default='proposed')
    manager_note = models.TextField(blank=True)
    alternate_date = models.DateField(null=True, blank=True)
    backup_participants = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='reviewed_assessment_sessions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=0)
    def __str__(self): return f'{self.date} {self.method}'

class SessionRevision(models.Model):
    session = models.ForeignKey(AssessmentSession, on_delete=models.CASCADE, related_name='history')
    revision = models.PositiveIntegerField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.TextField()
    impact = models.TextField(blank=True)
    followup_owner = models.CharField(max_length=160, blank=True)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['session','revision'], name='unique_session_revision')]
        ordering = ['-revision']

class OtherAudit(models.Model):
    evidence = models.OneToOneField(Evidence, on_delete=models.CASCADE, related_name='other_audit')
    scope = models.TextField()
    period_start = models.DateField()
    period_end = models.DateField()
    tested_control = models.TextField()
    finding = models.TextField()
    # Accepted TCA coverage remains in Coverage, clause by clause.

class Opportunity(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT, null=True, blank=True)
    kind = models.CharField(max_length=24, choices=[('documentation','Missing documentation'),('operational','Operational gap'),('verification','Pending verification'),('other','Other improvement')])
    problem = models.TextField()
    proposed_measure = models.TextField(blank=True)
    owner = models.CharField(max_length=160, blank=True)
    due_date = models.DateField(null=True, blank=True)
    priority_override = models.PositiveSmallIntegerField(null=True, blank=True)
    immediate_corrective = models.BooleanField(default=False)
    prerequisite = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='open')
    def __str__(self): return f'{self.requirement_id or "Other"}: {self.problem[:75]}'

class Kaizen(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    opportunity = models.ForeignKey(Opportunity, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200)
    profile = models.CharField(max_length=2, choices=[('A4','A4'),('A3','A3'),('BP','Business Process')])
    input_profile = models.CharField(max_length=10, default='legacy', choices=[('small','Small: quick PDCA'),('medium','Medium'),('extensive','Extensive'),('legacy','Legacy: size not classified')])
    local_status = models.CharField(max_length=12, default='open', choices=[('open','Open'),('closed','Locally closed')])
    status = models.CharField(max_length=28, default='proposed')
    revision = models.PositiveIntegerField(default=0)
    data = models.JSONField(default=dict)
    linked_requirements = models.ManyToManyField(Requirement, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.title

class KaizenAction(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='actions')
    phase = models.CharField(max_length=3, choices=[('DO','Do'),('ACT','Act')])
    description = models.TextField()
    owner = models.CharField(max_length=160)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    key_action = models.BooleanField(default=False)

class KaizenRevision(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='history')
    revision = models.PositiveIntegerField()
    state = models.CharField(max_length=28)
    snapshot = models.JSONField()
    reason = models.CharField(max_length=200)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-revision']
        constraints = [models.UniqueConstraint(fields=['event','revision'], name='unique_kaizen_revision')]

class ReviewNote(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='review_notes')
    stage = models.CharField(max_length=5, choices=[(s,s) for s in ('Plan','Do','Check','Act')])
    kind = models.CharField(max_length=12, choices=[('advice','Advice'),('clarify','Clarification'),('return','Changes requested'),('reply','Team reply')])
    text = models.TextField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    event_revision = models.PositiveIntegerField()
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='resolved_kaizen_notes')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at','pk']

class Participant(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='participants')
    first_initial = models.CharField(max_length=3)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    role_profile = models.CharField(max_length=100, blank=True)
    kaizen_role = models.CharField(max_length=100)
    estimated_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

class DocumentUpdate(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='document_updates')
    document_type = models.CharField(max_length=100)
    document_number = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=200)
    updated_at = models.DateField()

class Observation(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='observations')
    phase = models.CharField(max_length=6, choices=[('before','Before'),('after','After')])
    measure = models.CharField(max_length=160)
    value = models.DecimalField(max_digits=18, decimal_places=4)
    unit = models.CharField(max_length=60)
    population = models.CharField(max_length=160)
    period_start = models.DateField()
    period_end = models.DateField()
    data_source = models.TextField()

class Benefit(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='benefits')
    kind = models.CharField(max_length=20, choices=[('avoidance','Cost avoidance'),('savings','Realized savings'),('customer','Customer savings'),('hours','Time released'),('environment','Environmental')])
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    unit = models.CharField(max_length=40)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    validated = models.BooleanField(default=False)
    validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)

class AuditEvent(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=80)
    object_type = models.CharField(max_length=80)
    object_id = models.CharField(max_length=80)
    detail = models.JSONField(default=dict)

class Worksheet(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='worksheets')
    method = models.SlugField(max_length=40)
    schema_version = models.PositiveSmallIntegerField(default=1)
    stage = models.CharField(max_length=5)
    title = models.CharField(max_length=200)
    payload = models.JSONField(default=dict)
    revision = models.PositiveIntegerField(default=0)
    include_in_a3 = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

class WorksheetRevision(models.Model):
    worksheet = models.ForeignKey(Worksheet, on_delete=models.CASCADE, related_name='history')
    revision = models.PositiveIntegerField()
    schema_version = models.PositiveSmallIntegerField()
    payload = models.JSONField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-revision']
        constraints = [models.UniqueConstraint(fields=['worksheet','revision'], name='unique_worksheet_revision')]

class EventAttachment(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='attachments')
    stage = models.CharField(max_length=5)
    requirement = models.ForeignKey(Requirement, null=True, blank=True, on_delete=models.PROTECT)
    evidence = models.ForeignKey(Evidence, null=True, blank=True, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    original_name = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='kaizen/%Y/%m/', storage=PrivateLocalStorage(), blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    version = models.CharField(max_length=80)
    provenance = models.TextField()
    classification = models.CharField(max_length=20, default='internal', choices=Evidence._meta.get_field('classification').choices)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.title} · {self.original_name or "linked evidence"} · v{self.version}'

class ImportPreview(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='imports')
    attachment = models.ForeignKey(EventAttachment, on_delete=models.PROTECT)
    table = models.JSONField()
    mapping = models.JSONField(default=dict)
    confirmed = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class VerificationClaim(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT)
    event = models.ForeignKey(Kaizen, null=True, blank=True, on_delete=models.PROTECT)
    evidence = models.ManyToManyField(Evidence)
    status = models.CharField(max_length=10, default='pending')
    statement = models.TextField()
    decision = models.TextField(blank=True)
    revision = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='claims')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='claim_decisions')
    reviewed_at = models.DateTimeField(null=True)
    assessment = models.ForeignKey(Assessment, null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class A3Report(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='a3_reports')
    event_revision = models.PositiveIntegerField()
    renderer_version = models.PositiveSmallIntegerField(default=1)
    version = models.PositiveIntegerField()
    snapshot = models.JSONField()
    file = models.FileField(upload_to='reports/%Y/%m/', storage=PrivateLocalStorage())
    sha256 = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['event','version'], name='unique_a3_report_version')]

class LearningEntry(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.PROTECT)
    report = models.ForeignKey(A3Report, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    context = models.TextField()
    transfer_limits = models.TextField()
    approach = models.JSONField()
    allowed_sites = models.ManyToManyField(Site)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    approval_reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
