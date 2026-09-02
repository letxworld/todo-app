"""
Context processors for the Bug Bounty Tracker.

Add these to ``TEMPLATES[0]['OPTIONS']['context_processors']`` in
settings.py to make the data available in every template.

Currently exposes:
  * upcoming_deadlines -- tasks due within the next two days
"""

from datetime import timedelta

from django.utils import timezone

from core.models import Task


def upcoming_deadlines(request):
    """Return tasks whose deadline falls within the next 48 hours.

    Only includes tasks belonging to the logged-in user (or none if the
    user isn't authenticated).
    """
    if not request.user.is_authenticated:
        return {'upcoming_deadlines': []}

    now = timezone.now()
    window_end = now + timedelta(hours=48)

    tasks = (
        Task.objects
        .filter(asset__target__owner=request.user,
                deadline__isnull=False,
                deadline__gte=now,
                deadline__lte=window_end)
        .select_related('asset', 'asset__target')
        .order_by('deadline')[:10]
    )

    return {'upcoming_deadlines': tasks}
