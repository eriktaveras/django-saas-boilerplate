# AGENTS.md · django-saas-boilerplate

Boilerplate open source (MIT) para montar un SaaS con Django 6.0. Incluye usuario personalizado que entra solo con email (allauth), suscripciones con Stripe (Payment Methods API y webhook firmado), dashboard de usuario con perfil, ajustes y API keys hasheadas, y páginas públicas (home, features, pricing). Usa la CSP nativa con nonces y las tareas en segundo plano `@task` de Django 6.0.

## Stack

Python 3.12+, Django 6.0 (>=6.0,<6.2), django-allauth, Stripe SDK 15.x, django-htmx, WhiteNoise, Gunicorn, dj-database-url (SQLite en dev / PostgreSQL en prod). El frontend son plantillas Django con T

## Comandos

- Instalar: `uv venv venv --python 3.12 && uv pip install --python venv/bin/python -r requirements.txt  (equivale a `make install`, que usa python3 -m venv + pip y necesita python3.12-venv instalado en el sistema)`
- Tests: `DEBUG=True venv/bin/python manage.py test  (o `cp .env.example .env && make test`)`
- Build: `DEBUG=True venv/bin/python manage.py check && DEBUG=True venv/bin/python manage.py makemigrations --check --dry-run`
- Lint: `venv/bin/ruff check .  (make lint; para formatear: venv/bin/ruff format --check .)`

## Notas para agentes

No hay CI (.github/workflows ni .forgejo), ni AGENTS.md, ni Docker: la única verificación es local. El contexto principal está en CLAUDE.md. Todos los targets del Makefile usan ./venv. Sin SECRET_KEY y sin DEBUG=True, settings lanza ImproperlyConfigured, así que exporta DEBUG=True o copia .env.example a .env antes de ejecutar nada. Hay tests en apps/<app>/tests.py para accounts, dashboard, landing y subscriptions; los de Stripe usan mocks y no llaman a la red. El README habla de 46 tests: si añades tests, actualiza esa cifra. Convenciones: vistas basadas en funciones con @login_required y @require_http_methods; URLs con namespace (landing:, dashboard:); para FKs usa settings.AUTH_USER_MODEL y para consultas get_user_model(). En plantillas, todo <script> lleva nonce="{{ csp_nonce }}" y nada de handlers inline (onclick). Ruff: line-length 120, comillas simples, isort con apps/core como first-party. Las tareas van en apps/dashboard/tasks.py. requirements.txt tiene rangos fijados a propósito: no los abras. STRIPE_API_VERSION está fijada en core/settings.py.

---
Propuesto por el Taller de hermes-web a partir de su reconocimiento del repo; revísalo antes de fusionar.
