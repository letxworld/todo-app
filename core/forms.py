"""Forms for the Bug Bounty Target & Task Tracker.

Using Django ModelForms so the HTML fields are generated from the model
definitions — less code to maintain, and the validation rules stay in sync
with the database.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Target, Asset, Task, ASSET_TYPE_CHOICES, ASSET_STATUS_CHOICES, TASK_STATUS_CHOICES


class SignUpForm(UserCreationForm):
    """Registration form — reuses Django's built-in password checks."""
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class TargetForm(forms.ModelForm):
    class Meta:
        model = Target
        # `owner` is set from request.user in the view, never from the form.
        fields = ['name', 'platform', 'program_handle']
        labels = {
            'name': 'Program name (e.g. Acme Corp)',
            'platform': 'Platform (HackerOne / Bugcrowd / Other)',
            'program_handle': 'Program handle (used later for API scope import)',
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['domain_or_url', 'asset_type', 'status', 'in_scope']
        labels = {
            'domain_or_url': 'Domain or URL',
            'asset_type': 'Asset type',
            'status': 'Status',
            'in_scope': 'In scope?',
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'note', 'status', 'deadline']
        labels = {
            'title': 'Task title (e.g. Check for Open Redirect)',
            'note': 'Notes — findings, payloads tried, evidence',
            'status': 'Status',
            'deadline': 'Deadline (leave blank if none)',
        }
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }
