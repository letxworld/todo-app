from django.db import migrations


# The default vulnerability checklist. Applying it to an Asset creates one
# Task per item, so a hunter doesn't re-type the same checks for every asset.
DEFAULT_CHECKLIST = [
    ("XSS", "Test for reflected, stored, and DOM-based cross-site scripting."),
    ("IDOR", "Look for insecure direct object references / broken access control on object IDs."),
    ("Open Redirect", "Find any parameter that lets you redirect to an external domain."),
    ("SSRF", "Try to make the server fetch internal/cloud metadata URLs."),
    ("CSRF", "Check state-changing requests lack anti-CSRF tokens / same-site protection."),
    ("Auth Bypass", "Test login, 2FA, password reset, and parameter tampering for auth flaws."),
    ("SQL Injection", "Probe inputs for SQL injection / blind injection."),
    ("Broken Access Control", "Verify a user can't reach another user's data or admin functions."),
    ("Sensitive Data Exposure", "Look for secrets, PII, or tokens leaked in responses/source."),
    ("Rate Limiting", "Check brute-force / enumeration endpoints lack rate limiting."),
]


def create_default_checklists(apps, schema_editor):
    ChecklistTemplate = apps.get_model('core', 'ChecklistTemplate')
    for title, description in DEFAULT_CHECKLIST:
        ChecklistTemplate.objects.get_or_create(
            title=title,
            defaults={'description': description, 'is_default': True},
        )


def remove_default_checklists(apps, schema_editor):
    ChecklistTemplate = apps.get_model('core', 'ChecklistTemplate')
    ChecklistTemplate.objects.filter(is_default=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_checklists, remove_default_checklists),
    ]
