"""
Django signals for the Bug Bounty Tracker.

Currently:
  * Auto-set ``date_completed`` when a Task flips to ``found`` or ``no_vuln``.
    (The view layer already does this in task_edit, but the signal covers any
    other path that might update a task status, e.g. bulk actions in the admin.)
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from core.models import Task


@receiver(pre_save, sender=Task)
def stamp_completion_on_findings(sender, instance: Task, **kwargs):
    """Set ``date_completed`` when status becomes ``found`` or ``no_vuln``.

    Only stamps when the field is currently empty -- avoids overwriting a
    real manual completion timestamp if the user flips back and forth.
    """
    if instance.status in ('found', 'no_vuln') and not instance.date_completed:
        from django.utils import timezone
        instance.date_completed = timezone.now()
