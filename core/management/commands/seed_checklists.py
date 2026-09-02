"""
Re-seed the default vulnerability checklist.

Call this after adding new default items to the migration or whenever you
want to make sure all ``is_default=True`` templates exist in the DB.

Usage::

    python manage.py seed_checklists
"""

from django.core.management.base import BaseCommand

from core.models import ChecklistTemplate

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


class Command(BaseCommand):
    help = 'Ensure the default vulnerability checklist items exist in the database'

    def handle(self, *args, **options):
        created = 0
        for title, description in DEFAULT_CHECKLIST:
            obj, was_created = ChecklistTemplate.objects.get_or_create(
                title=title,
                defaults={'description': description, 'is_default': True},
            )
            if was_created:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(f'Default checklist ready ({created} new items created).')
        )
