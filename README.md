# Django SaaS Boilerplate

The open-source Django starter kit for building SaaS applications. Auth, payments, dashboard, and deployment — all wired up.

<div align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django"/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-CDN-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS"/>
  <img src="https://img.shields.io/badge/Stripe-Payments-6772E5?style=for-the-badge&logo=stripe&logoColor=white" alt="Stripe"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT"/>
</div>

---

## What this is

A small, finished SaaS starter. Sign up, log in, land on a dashboard, pay with a
card, and there is a public site in front of it. That is the whole scope, and it
is deliberate: it is what you need on a Saturday morning to stop configuring and
start building the thing you actually wanted to build.

Everything below works out of the box.

- **Custom user model** — email-only login, no username
- **Authentication** — signup, login, email verification, password reset (django-allauth), 21 styled templates
- **Stripe subscriptions** — Payment Methods API, pinned API version, signed webhook, subscription status on the user
- **User dashboard** — sidebar nav, profile, notification settings, API key generation (hashed, shown once)
- **Subscription plans** — admin-managed plans with trial support
- **Landing pages** — home, features, pricing, `robots.txt`
- **Background tasks** — Django 6.0 native `@task()`, no Celery
- **Content Security Policy** — Django 6.0 CSP middleware with nonces
- **Security headers** — HSTS, SSL redirect, secure cookies (auto-enabled in production)
- **PostgreSQL support** — `DATABASE_URL` with SQLite fallback
- **Static files** — WhiteNoise, no nginx needed
- **Deployment** — Gunicorn + Procfile, ready for Railway/Heroku/VPS
- **Linting** — Ruff with Django-specific rules
- **46 tests** — landing pages, auth, dashboard, models, Stripe checkout and webhook
- **Seed data** — one command to populate demo data

## What it does not do

Worth knowing before you build on it, so you can decide what to add yourself:

- **No teams or multi-tenancy.** One user, one account. There is no concept of
  an organisation, a member, or a role.
- **No plan gating.** `SubscriptionPlan.features` is a JSON list for the pricing
  page — marketing copy, not entitlements. Nothing in the code stops a free user
  from using a paid feature, and there are no usage counters or quotas.
- **Two places track a subscription.** `StripeCustomer` mirrors Stripe;
  `UserSettings` holds the plan and trial the dashboard reads. Nothing
  reconciles them, so the dashboard's manual plan/trial actions do not touch
  Stripe. Wiring them together is left to you.
- **Minimal billing lifecycle.** The webhook handles subscription
  created/updated/deleted. No failed-payment recovery, no customer portal, no
  invoice history.
- **No REST API.** The dashboard mints and hashes an API key, but nothing
  authenticates with it yet — it is a starting point, not an API.
- **Tailwind and Alpine come from a CDN.** No build step, which is why setup is
  one command. Before production you will want a real Tailwind build.
- **No Docker, no CI.** `make run` and a Procfile.

MIT licensed. Fork it, rename it, ship it, sell it — no attribution required.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6.0, Python 3.12 |
| Auth | django-allauth (email-only) |
| Payments | Stripe (Payment Methods API) |
| Frontend | Tailwind CSS (CDN), Alpine.js, HTMX |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Static files | WhiteNoise |
| Server | Gunicorn |
| Tasks | Django 6.0 native `@task()` |
| Linting | Ruff |

## Quick start

```bash
git clone https://github.com/eriktaveras/django-saas-boilerplate.git
cd django-saas-boilerplate
make install
cp .env.example .env
make migrate
python manage.py seed_data
make run
```

Visit **http://localhost:8000**. `seed_data` prints the generated admin password once — copy it from the terminal. Set `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` to choose your own.

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Create virtualenv and install dependencies |
| `make run` | Start development server |
| `make migrate` | Run makemigrations + migrate |
| `make test` | Run 46 tests |
| `make seed` | Populate demo data (admin + plans) |
| `make lint` | Lint with ruff |
| `make format` | Format with ruff |
| `make superuser` | Create admin user |
| `make clean` | Remove __pycache__ files |

## Project structure

```
django-saas-boilerplate/
├── core/
│   ├── settings.py           # All config via env vars
│   ├── urls.py               # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/             # CustomUser (email-only), admin
│   │   ├── models.py         # CustomUser + CustomUserManager
│   │   ├── admin.py
│   │   └── tests.py          # 6 tests
│   ├── dashboard/            # Dashboard, profile, settings
│   │   ├── models.py         # SubscriptionPlan, UserSettings
│   │   ├── views.py          # dashboard, profile, settings, plans
│   │   ├── tasks.py          # Background email tasks
│   │   ├── tests.py          # 6 tests
│   │   └── management/commands/seed_data.py
│   ├── subscriptions/        # Stripe integration
│   │   ├── models.py         # StripeCustomer
│   │   ├── views.py          # checkout, webhooks
│   │   └── tests.py          # 10 tests
│   └── landing/              # Public pages
│       ├── views.py          # home, features, pricing, robots.txt
│       └── tests.py          # 4 tests
├── templates/
│   ├── base.html             # Public layout (nav + footer)
│   ├── account/              # 21 allauth templates (styled)
│   ├── dashboard/            # Dashboard layout + pages
│   ├── landing/              # Home, features, pricing
│   └── subscriptions/        # Stripe checkout
├── static/css/               # Design system CSS
├── CLAUDE.md                 # AI editor context
├── Makefile                  # Dev commands
├── Procfile                  # Deployment
├── pyproject.toml            # Ruff config
├── requirements.txt
└── .env.example
```

## Environment variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
DEBUG=True
SECRET_KEY=your-secret-key

# Database (default: SQLite)
# DATABASE_URL=postgres://user:password@localhost:5432/dbname

# Stripe (required for payments)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...

# Email (default: console backend)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
```

## Django 6.0 features used

This boilerplate uses two features introduced in Django 6.0:

**Background Tasks** — Send emails asynchronously without Celery:
```python
from django.tasks import task

@task
def send_welcome_email(user_email):
    send_mail("Welcome!", "...", None, [user_email])

# In your view:
send_welcome_email.enqueue(user_email=user.email)
```

**Content Security Policy** — Built-in CSP middleware with nonce support:
```python
SECURE_CSP = {
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
}
```
```html
<script nonce="{{ csp_nonce }}" src="..."></script>
```

## Deployment

### Railway

Push to GitHub and connect to Railway. The `Procfile` and `DATABASE_URL` handling are already configured.

### Heroku

```bash
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
git push heroku main
heroku run python manage.py migrate
```

### VPS

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
gunicorn core.wsgi --bind 0.0.0.0:8000
```

## If you need the other half

Some of what is missing above is a weekend of work. Some of it is not — plan
gating, dunning and GDPR flows are the parts that quietly eat a month.

[**DjangoBlaze**](https://djangoblaze.com) is the paid version of this
boilerplate, and it is where that work already lives:

- Teams and multi-tenancy
- Per-plan feature gating with usage limits
- REST API with hashed keys
- AI chat
- Blog with SEO
- Two-factor authentication
- Dunning (failed-payment recovery)
- GDPR account deletion and data export
- Docker, CI
- 24 AI skills for working on the codebase

8 apps, 203 tests. $99 one time, unlimited projects, one year of updates.

No pressure either way — this repo is MIT and stays that way.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Author

**Erik Taveras** — Full Stack Developer

- [eriktaveras.com](https://www.eriktaveras.com)
- [github.com/eriktaveras](https://github.com/eriktaveras)
- [hello@eriktaveras.com](mailto:hello@eriktaveras.com)

---

## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=eriktaveras/django-saas-boilerplate&type=date&legend=top-left)](https://www.star-history.com/?repos=eriktaveras%2Fdjango-saas-boilerplate&type=date&legend=top-left)
