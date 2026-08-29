"""URL configuration for the core app.

Routes are split into two groups:
  * auth (login / logout / signup) — public
  * everything else — protected with @login_required in views.py
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # --- Authentication -----------------------------------------------------
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.signup, name='signup'),

    # --- Targets (bug bounty programs) ------------------------------------
    path('', views.dashboard, name='dashboard'),
    path('target/new/', views.target_create, name='target_create'),
    path('target/<int:pk>/', views.target_detail, name='target_detail'),
    path('target/<int:pk>/edit/', views.target_edit, name='target_edit'),
    path('target/<int:pk>/delete/', views.target_delete, name='target_delete'),

    # --- Assets (in-scope items inside a target) --------------------------
    path('target/<int:target_pk>/asset/new/', views.asset_create, name='asset_create'),
    path('asset/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('asset/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('asset/<int:pk>/delete/', views.asset_delete, name='asset_delete'),

    # --- Checklist (reusable vuln list applied to an asset) ---------------
    path('asset/<int:pk>/apply-checklist/', views.apply_checklist, name='apply_checklist'),

    # --- Tasks (testing actions on an asset) ------------------------------
    path('asset/<int:asset_pk>/task/new/', views.task_create, name='task_create'),
    path('task/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete'),

    # --- Findings log (all completed/found tasks across targets) ----------
    path('findings/', views.findings, name='findings'),
]
