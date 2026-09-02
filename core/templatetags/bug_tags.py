"""
Custom template tags for the Bug Bounty Tracker.

Load with ``{% load bug_tags %}`` in any template.
"""

from django import template

from core.models import ASSET_STATUS_CHOICES, TASK_STATUS_CHOICES

register = template.Library()


@register.inclusion_tag('core/_status_badge.html')
def status_badge(status: str, kind: str = 'task') -> dict:
    """Render a small coloured badge for a task/asset status value.

    Usage::

        {% status_badge task.status 'task' %}
        {% status_badge asset.status 'asset' %}

    The tag picks a coloured pill from a small mapping; unrecognised values
    render as a neutral grey pill.
    """
    display = _display_for(status, kind)
    colour = _colour_for(status, kind)
    return {'status': status, 'display': display, 'colour': colour}


def _display_for(status: str, kind: str) -> str:
    """Human-readable label for a status code."""
    choices = TASK_STATUS_CHOICES if kind == 'task' else ASSET_STATUS_CHOICES
    for val, label in choices:
        if val == status:
            return label
    return status


def _colour_for(status: str, kind: str) -> str:
    """CSS colour token for a status code."""
    if kind == 'task':
        return {
            'found': 'var(--ok)',
            'no_vuln': 'var(--muted)',
            'testing': 'var(--accent)',
            'not_started': 'var(--muted)',
        }.get(status, 'var(--muted)')
    # asset
    return {
        'reported': 'var(--ok)',
        'testing': 'var(--accent)',
        'recon': 'var(--accent)',
        'not_started': 'var(--muted)',
    }.get(status, 'var(--muted)')
