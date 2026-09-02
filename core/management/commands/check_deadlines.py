"""
Check for tasks whose deadline is approaching or has passed.

Designed to be run from cron / a scheduler.  Prints a line per task that
needs attention; exit code 0 means "no problems", 1 means "issues found"
so a wrapper script can alert on non-zero.

Usage::

    python manage.py check_deadlines            # check all
    python manage.py check_deadlines --hours 48  # only tasks due within 48h
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Task


class Command(BaseCommand):
    help = 'List tasks with deadlines that are past due or approaching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=None,
            help='Only report tasks due within this many hours from now (default: report everything past due + next 48h)',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        hours = options['hours']
        if hours is None:
            # Default window: past due + next 48 hours.
            since = now - timedelta(days=2)
            till = now + timedelta(days=2)
        else:
            since = now
            till = now + timedelta(hours=hours)

        tasks = (
            Task.objects
            .filter(deadline__isnull=False)
            .select_related('asset', 'asset__target')
            .filter(deadline__gte=since, deadline__lte=till)
            .order_by('deadline')
        )

        found = False
        for task in tasks:
            found = True
            delta = task.deadline - now
            hours_left = int(delta.total_seconds() / 3600)
            if task.deadline < now:
                status_line = self.style.WARNING('OVERDUE')
            elif hours_left <= 24:
                status_line = self.style.WARNING('DUE SOON')
            else:
                status_line = self.style.SUCCESS('UPCOMING')
            self.stdout.write(
                f'[{status_line}] {task.asset.target.name} / {task.asset.domain_or_url} / '
                f'{task.title} -- deadline {task.deadline.strftime("%Y-%m-%d %H:%M")} '
                f'({hours_left}h left)'
            )

        if not found:
            self.stdout.write(self.style.SUCCESS('No deadlines in the checked window.'))
