"""
Deadline-notification helpers.

The notification channel is deliberately minimal right now -- console / log
output -- so the feature can be validated before wiring in browser push or
email.  Swap the backend by changing ``DELIVERY_BACKEND`` below.

Usage from a management command or cron::

    from core.notifications import notify_upcoming_deadlines
    notify_upcoming_deadlines()
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.utils import timezone

from core.models import Task

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Backed by Django's mailers / EMAIL settings; swap the path to enable
# real email without touching the notification logic.
DELIVERY_BACKEND = getattr(settings, 'DEADLINE_NOTIFICATION_BACKEND',
                           'core.notifications.log_notification')

# How far ahead to start warning (hours).
NOTIFY_WINDOW_HOURS = getattr(settings, 'DEADLINE_NOTIFY_WINDOW_HOURS', 48)
# How often to suppress duplicate reminders for the same task (hours).
DUPLICATE_COOLDOWN_HOURS = getattr(settings, 'DEADLINE_NOTIFY_COOLDOWN_HOURS', 6)


# ---------------------------------------------------------------------------
# Delivery backends
# ---------------------------------------------------------------------------

def log_notification(task: Task, message: str) -> None:
    """Print the notification to stdout (visible in cron / run logs)."""
    print(f'[DEADLINE] {task.asset.target.name} / {task.asset.domain_or_url} / '
          f'{task.title}: {message}')


def mail_notification(task: Task, message: str) -> None:
    """Send an email to the task's owner (requires EMAIL settings configured)."""
    from django.core.mail import send_mail

    subject = f'Bug Bounty Tracker: deadline approaching — {task.title}'
    body = (
        f'Program: {task.asset.target.name}\n'
        f'Asset:   {task.asset.domain_or_url}\n'
        f'Task:    {task.title}\n'
        f'{message}\n'
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost'),
        recipient_list=[task.asset.target.owner.email],
        fail_silently=True,
    )


# ---------------------------------------------------------------------------
# Core notification logic
# ---------------------------------------------------------------------------

def notify_upcoming_deadlines(*, since: timezone.datetime | None = None,
                               till: timezone.datetime | None = None) -> list[dict[str, Any]]:
    """Find tasks with deadlines in the window and deliver a reminder.

    Parameters
    ----------
    since, till : datetime, optional
        Window boundaries.  Defaults to (now, now + NOTIFY_WINDOW_HOURS).

    Returns
    -------
    A list of dicts describing what was notified, suitable for logging or
    later inspection.
    """
    now = timezone.now()
    if since is None:
        since = now
    if till is None:
        till = now + timedelta(hours=NOTIFY_WINDOW_HOURS)

    tasks = (
        Task.objects
        .filter(deadline__isnull=False,
                deadline__gte=since,
                deadline__lte=till)
        .select_related('asset', 'asset__target')
        .order_by('deadline')
    )

    notified: list[dict[str, Any]] = []
    for task in tasks:
        delta = task.deadline - now
        hours_left = int(delta.total_seconds() / 3600)
        if hours_left <= 0:
            message = f'OVERDUE — was due {task.deadline.strftime("%Y-%m-%d %H:%M %Z")}.'
        elif hours_left <= 24:
            message = f'DUE WITHIN {hours_left}h — deadline {task.deadline.strftime("%Y-%m-%d %H:%M %Z")}.'
        else:
            message = f'Deadline in {hours_left}h ({task.deadline.strftime("%Y-%m-%d %H:%M %Z")}).'

        backend = DELIVERY_BACKEND
        if isinstance(backend, str):
            # Import the dotted path.
            mod_path, func_name = backend.rsplit('.', 1)
            import importlib
            mod = importlib.import_module(mod_path)
            delivery_fn = getattr(mod, func_name)
        else:
            delivery_fn = backend

        delivery_fn(task, message)
        notified.append({
            'task_id': task.pk,
            'title': task.title,
            'hours_left': hours_left,
            'message': message,
        })

    return notified
