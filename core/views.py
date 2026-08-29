"""
Views for the Bug Bounty Target & Task Tracker.

This is the custom frontend (plain Django Templates, no React by design).

Per-user data scoping — a core requirement:
    Target.owner is a ForeignKey to the User. Every query filters by
    request.user so a logged-in hunter only ever sees / edits THEIR OWN
    targets, assets, and tasks.
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from .forms import TargetForm, AssetForm, TaskForm, SignUpForm
from .models import Target, Asset, Task, ChecklistTemplate


# --- Authentication -------------------------------------------------------

def signup(request):
    """Public registration. Creates a User, then drops them at the login page."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})


# --- Targets --------------------------------------------------------------

@login_required
def dashboard(request):
    """Landing page after login: the user's bug bounty programs."""
    targets = Target.objects.filter(owner=request.user)
    return render(request, 'core/dashboard.html', {'targets': targets})


@login_required
def target_create(request):
    if request.method == 'POST':
        form = TargetForm(request.POST)
        if form.is_valid():
            target = form.save(commit=False)
            target.owner = request.user
            target.save()
            return redirect('dashboard')
    else:
        form = TargetForm()
    return render(request, 'core/target_form.html', {'form': form, 'mode': 'new'})


@login_required
def target_detail(request, pk):
    target = get_object_or_404(Target, pk=pk, owner=request.user)
    return render(request, 'core/target_detail.html', {'target': target})


@login_required
def target_edit(request, pk):
    target = get_object_or_404(Target, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = TargetForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            return redirect('target_detail', pk=target.pk)
    else:
        form = TargetForm(instance=target)
    return render(request, 'core/target_form.html', {'form': form, 'mode': 'edit', 'target': target})


@login_required
def target_delete(request, pk):
    target = get_object_or_404(Target, pk=pk, owner=request.user)
    if request.method == 'POST':
        target.delete()
        return redirect('dashboard')
    return render(request, 'core/confirm_delete.html', {
        'object': target, 'back_url': 'dashboard',
    })


# --- Assets ---------------------------------------------------------------

@login_required
def asset_create(request, target_pk):
    target = get_object_or_404(Target, pk=target_pk, owner=request.user)
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.target = target
            asset.save()
            return redirect('target_detail', pk=target.pk)
    else:
        form = AssetForm()
    return render(request, 'core/asset_form.html', {'form': form, 'target': target, 'mode': 'new'})


@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk, target__owner=request.user)
    return render(request, 'core/asset_detail.html', {'asset': asset})


@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk, target__owner=request.user)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            return redirect('asset_detail', pk=asset.pk)
    else:
        form = AssetForm(instance=asset)
    return render(request, 'core/asset_form.html', {'form': form, 'target': asset.target, 'mode': 'edit', 'asset': asset})


@login_required
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk, target__owner=request.user)
    target_pk = asset.target.pk
    if request.method == 'POST':
        asset.delete()
        return redirect('target_detail', pk=target_pk)
    return render(request, 'core/confirm_delete.html', {
        'object': asset, 'back_url': 'target_detail', 'back_pk': target_pk,
    })


@login_required
def apply_checklist(request, pk):
    """Create one Task per checklist item for this asset (the key feature)."""
    asset = get_object_or_404(Asset, pk=pk, target__owner=request.user)
    if request.method == 'POST':
        selected = request.POST.getlist('checklist')
        templates = ChecklistTemplate.objects.filter(pk__in=selected)
        created = 0
        for tmpl in templates:
            # Avoid duplicating a task that already exists for this asset+title.
            if not Task.objects.filter(asset=asset, title=tmpl.title).exists():
                Task.objects.create(asset=asset, title=tmpl.title, note=tmpl.description)
                created += 1
        return redirect('asset_detail', pk=asset.pk)
    templates = ChecklistTemplate.objects.all()
    return render(request, 'core/apply_checklist.html', {'asset': asset, 'templates': templates})


# --- Tasks ----------------------------------------------------------------

@login_required
def task_create(request, asset_pk):
    asset = get_object_or_404(Asset, pk=asset_pk, target__owner=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.asset = asset
            task.save()
            return redirect('asset_detail', pk=asset.pk)
    else:
        form = TaskForm()
    return render(request, 'core/task_form.html', {'form': form, 'asset': asset, 'mode': 'new'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, asset__target__owner=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            # Auto-stamp completion date when status flips to found / no_vuln.
            updated = form.save(commit=False)
            if updated.status in ('found', 'no_vuln') and not updated.date_completed:
                from django.utils import timezone
                updated.date_completed = timezone.now()
            updated.save()
            return redirect('asset_detail', pk=task.asset.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'core/task_form.html', {'form': form, 'asset': task.asset, 'mode': 'edit', 'task': task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, asset__target__owner=request.user)
    asset_pk = task.asset.pk
    if request.method == 'POST':
        task.delete()
        return redirect('asset_detail', pk=asset_pk)
    return render(request, 'core/confirm_delete.html', {
        'object': task, 'back_url': 'asset_detail', 'back_pk': asset_pk,
    })


# --- Findings log ---------------------------------------------------------

@login_required
def findings(request):
    """All completed/found tasks across every target — a personal findings history."""
    tasks = (
        Task.objects
        .filter(asset__target__owner=request.user, status__in=('found', 'no_vuln'))
        .select_related('asset', 'asset__target')
    )
    return render(request, 'core/findings.html', {'tasks': tasks})
