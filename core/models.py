from django.db import models
from django.contrib.auth.models import User


# Shared status constants -------------------------------------------------
# Keeping them here means views/forms/templates can import the same list
# instead of each hard-coding their own strings.

TARGET_STATUS = []  # Targets don't need a workflow status (yet).

ASSET_STATUS_CHOICES = [
    ('not_started', 'Not started'),
    ('recon', 'Recon'),
    ('testing', 'Testing'),
    ('reported', 'Reported'),
]

TASK_STATUS_CHOICES = [
    ('not_started', 'Not started'),
    ('testing', 'Testing'),
    ('found', 'Found'),
    ('no_vuln', 'No vuln'),
]

ASSET_TYPE_CHOICES = [
    ('web', 'Web'),
    ('mobile', 'Mobile'),
    ('api', 'API'),
    ('other', 'Other'),
]


class Target(models.Model):
    """A bug bounty program the user is hunting on."""
    name = models.CharField(max_length=255, help_text="e.g. Acme Corp")
    platform = models.CharField(
        max_length=100,
        help_text="HackerOne / Bugcrowd / Intigriti / Other",
    )
    program_handle = models.CharField(
        max_length=255,
        blank=True,
        help_text="Program handle, used later for API scope-fetching",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='targets',
        help_text="The user this program belongs to",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Asset(models.Model):
    """A single in-scope (or out-of-scope) item inside a Target."""
    target = models.ForeignKey(
        Target, on_delete=models.CASCADE, related_name='assets'
    )
    domain_or_url = models.CharField(max_length=255)
    asset_type = models.CharField(
        max_length=50, choices=ASSET_TYPE_CHOICES, default='web'
    )
    status = models.CharField(
        max_length=50, choices=ASSET_STATUS_CHOICES, default='not_started'
    )
    in_scope = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['domain_or_url']

    def __str__(self):
        return self.domain_or_url


class Task(models.Model):
    """A specific testing action/check performed against an Asset."""
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='tasks'
    )
    title = models.CharField(max_length=255, help_text="e.g. Check for Open Redirect")
    note = models.TextField(
        blank=True, help_text="Findings, payloads tried, evidence"
    )
    status = models.CharField(
        max_length=50, choices=TASK_STATUS_CHOICES, default='not_started'
    )
    deadline = models.DateTimeField(null=True, blank=True)
    date_completed = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-deadline', 'title']

    def __str__(self):
        return self.title


class ChecklistTemplate(models.Model):
    """A reusable vulnerability-checklist item.

    Applying a checklist to an Asset auto-creates one Task per template,
    so a hunter doesn't have to type the same checks for every asset.
    """
    title = models.CharField(max_length=255, help_text="e.g. XSS")
    description = models.TextField(
        blank=True, help_text="Short reminder of what to test"
    )
    is_default = models.BooleanField(
        default=False, help_text="Default items are seeded once on first run"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title
