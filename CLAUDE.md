# Django SaaS Boilerplate

## Overview
Django SaaS boilerplate with Stripe subscriptions, email authentication, and a modern frontend. Built with Django 6.0 and Python 3.12.

## Tech Stack
- **Backend:** Django 6.0, Python 3.12
- **Auth:** django-allauth (email-only, no username)
- **Payments:** Stripe (Payment Methods API)
- **Frontend:** Tailwind CSS (CDN) + Alpine.js + HTMX
- **Database:** SQLite (dev) / PostgreSQL via `DATABASE_URL` (prod)
- **Static Files:** WhiteNoise
- **Server:** Gunicorn
- **Background Tasks:** Django 6.0 native `@task()` decorator
- **Linting:** Ruff

## Project Structure
```
core/           → Settings, URLs, WSGI/ASGI
apps/
  accounts/     → CustomUser model (email-only), admin
  dashboard/    → Dashboard, profile, settings, subscription management
  landing/      → Public pages (home, pricing, features), robots.txt
  subscriptions/→ Stripe integration, webhooks
templates/      → All HTML templates (Tailwind + Alpine.js)
static/         → CSS, JS, images
```

## Key Conventions

### User Model
- Custom user model at `apps.accounts.CustomUser` — email-only, no username
- Use `settings.AUTH_USER_MODEL` for ForeignKey/OneToOneField references
- Use `get_user_model()` for queries

### Views
- Function-based views with `@login_required` and `@require_http_methods` decorators
- App-specific URL namespaces: `landing:home`, `dashboard:home`, `dashboard:profile`, etc.

### Django 6.0 Features
- **CSP:** Configured via `SECURE_CSP` in settings, nonces available as `{{ csp_nonce }}` in templates
- **Background Tasks:** Use `@task` decorator, enqueue with `.enqueue()` — see `apps/dashboard/tasks.py`
- **Template Partials:** Use `{% partialdef name inline %}` and `{% partial name %}` for reusable components

### Templates
- Design system: monochromatic (black/white/gray), Space Grotesk font, uppercase tracking
- All external scripts/styles use `nonce="{{ csp_nonce }}"` for CSP
- Two base templates: `templates/base.html` (public) and `templates/dashboard/base.html` (authenticated)

## Commands
```bash
make install    # Create venv and install dependencies
make run        # Start development server
make migrate    # Run makemigrations + migrate
make test       # Run tests
make seed       # Populate demo data (admin + plans)
make lint       # Lint with ruff
make format     # Format with ruff
make superuser  # Create admin user
```

## Environment
Copy `.env.example` to `.env`. Key variables:
- `SECRET_KEY` — Django secret key
- `DATABASE_URL` — PostgreSQL connection (default: SQLite)
- `STRIPE_*` — Stripe API keys
- `EMAIL_*` — SMTP configuration
