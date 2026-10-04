from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from .storage import PrivateLocalStorage

class Site(models.Model):
    name = models.CharField(max_length=180, unique=True)
    code = models.SlugField(unique=True)
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
    policy_version = models.CharField(max_length=20, default='draft-v1')
    rationale = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_assessments')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='approved_assessments')
    approved_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=0)
    snapshot = models.JSONField(default=dict)  # frozen accepted coverage and category results at approval
    class Meta:
        constraints = [models.UniqueConstraint(fields=['site','version'], name='unique_site_assessment_version')]
        ordering = ['-version']

class Response(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='responses')
    requirement = models.ForeignKey(Requirement, on_delete=models.PROTECT)
    code = models.CharField(max_length=1, choices=[('Y','Yes'),('N','No'),('A','Unresolved A'),('','Unanswered')], blank=True)
    conclusion = models.TextField(blank=True)
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
    def __str__(self): return f'{self.date} {self.method}'

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
    status = models.CharField(max_length=28, default='proposed')
    revision = models.PositiveIntegerField(default=0)
    data = models.JSONField(default=dict)
    linked_requirements = models.ManyToManyField(Requirement, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class KaizenAction(models.Model):
    event = models.ForeignKey(Kaizen, on_delete=models.CASCADE, related_name='actions')
    phase = models.CharField(max_length=3, choices=[('DO','Do'),('ACT','Act')])
    description = models.TextField()
    owner = models.CharField(max_length=160)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    key_action = models.BooleanField(default=False)

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
