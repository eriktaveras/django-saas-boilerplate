# Django SaaS Boilerplate

## Overview
Django SaaS boilerplate with Stripe subscriptions, email authentication, and a modern frontend. Built with Django >=6.0,<6.2 and Python 3.12+.

## Tech Stack
- **Backend:** Django >=6.0,<6.2, Python 3.12+
- **Auth:** django-allauth (email-only, no username)
- **Payments:** Stripe SDK >=15,<16 (Payment Methods API), API version configured in `core/settings.py`
- **Frontend:** Tailwind CSS (CDN) + Alpine.js + HTMX
- **Database:** SQLite (dev) / PostgreSQL via `DATABASE_URL` (prod)
- **Static Files:** WhiteNoise
- **Server:** Gunicorn
- **Tasks:** Django 6.0 native `@task()` decorator with ImmediateBackend (synchronous execution)
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
- **Tasks:** Use `@task` decorator, enqueue with `.enqueue()` — see `apps/dashboard/tasks.py`. The configured ImmediateBackend runs tasks immediately in the calling process; no worker or durable queue is configured

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

## Subscription behavior
- See [apps/subscriptions/README.md](apps/subscriptions/README.md) for checkout and webhook details.
- Supported events: `customer.subscription.created`, `.updated`, and `.deleted` only; no invoice payment handlers.
- `StripeCustomer` stores Stripe identifiers/status; `_sync_access` mirrors status and available dates into `UserSettings`.
- A late `created` event cannot overwrite an already linked subscription. An unlinked customer can be linked only for the configured price.
- Direct free-plan and trial POSTs create missing settings. Paid plans redirect to checkout. Trials last 14 days and cannot be repeated once `trial_end_date` is set.
- Paid cancellation sets `cancel_at_period_end=True` at Stripe; local cancellation applies immediately when no Stripe subscription is linked.

## Local validation
All Makefile targets use `./venv`. Install with `make install` (requires Python 3.12+ and OS venv support), or:

```bash
uv venv venv --python 3.12
uv pip install --python venv/bin/python -r requirements.txt
DEBUG=True venv/bin/python manage.py test
DEBUG=True venv/bin/python manage.py check
DEBUG=True venv/bin/python manage.py makemigrations --check --dry-run
venv/bin/ruff check .
```

See [README: Local validation](README.md#local-validation) for the test count and breakdown.
Stripe tests mock network calls. Validation is local; no CI workflows are configured.
Without `DEBUG=True`, `SECRET_KEY` is required. Email defaults to console in debug and SMTP otherwise.
PostgreSQL needs an additional driver such as psycopg; requirements do not install one.
Keep dependency ranges and the Stripe API version pinned. No frontend build is configured: templates load CDN assets.
