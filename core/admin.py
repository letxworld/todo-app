"""Admin panel registrations.

Used during development to view / add / edit data directly without building
custom UI first. `list_display` makes each model's list page actually readable.
"""

from django.contrib import admin

from .models import Target, Asset, Task, ChecklistTemplate


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'program_handle', 'owner', 'created_at']
    list_filter = ['platform', 'owner']
    search_fields = ['name', 'program_handle']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['domain_or_url', 'target', 'asset_type', 'status', 'in_scope']
    list_filter = ['asset_type', 'status', 'in_scope']
    search_fields = ['domain_or_url']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'asset', 'status', 'deadline', 'date_completed']
    list_filter = ['status']
    search_fields = ['title', 'note']


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_default', 'created_at']
    list_filter = ['is_default']
    search_fields = ['title']
