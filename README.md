# Bug Bounty Target & Task Tracker

A workflow tracker built for bug bounty hunters — tracks programs (Targets),
their in-scope assets (Assets), and testing tasks against each asset. Plain
Django + Templates, no React (by design).

## Stack
- Django 6.1, SQLite, Django's built-in auth, Django admin for raw data work.

## Run it locally
    cd todo-app
    source venv/bin/activate
    python manage.py migrate
    python manage.py runserver
    # open http://localhost:8000  (sign up for an account)

## What's built (MVP)
- Signup / login / logout (per-user data scoping).
- Target CRUD (bug bounty programs) with platform + program handle.
- Asset CRUD (in-scope items) with type/status/scope flags.
- Task CRUD per asset, with notes, status, deadline, and auto completion date.
- Reusable vulnerability checklist: apply the seeded XSS/IDOR/SSRF/... list to
  any asset to auto-create one Task per item.
- Findings log: a personal history of all completed / found tasks.
- Admin panel for direct data inspection.

## Not yet built (per the project plan)
- Automatic scope import (HackerOne API / CSV upload / manual paste + review screen).
- Deadline notifications (browser / email / in-app).
- AI features (next-step suggestions, report drafting).
- React frontend via DRF.
