# Security

## Reporting a vulnerability

Email **hello@eriktaveras.com**. Please do not open a public issue for a
security problem. I will confirm receipt and tell you what I plan to do.

## If you deployed a version from before September 2026

Two defaults in this repository were published values, and a deployment made
from an earlier version still carries them. Both are fixed on `main`, but a
fork or an existing deployment does not pick that up on its own.

### 1. Rotate your `SECRET_KEY`

`core/settings.py` used to fall back to a key committed to this repository. If
you deployed without setting the `SECRET_KEY` environment variable, your
installation is running with a key that anyone can read here, and with it an
attacker can forge session cookies and password-reset tokens for your site.

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Set that as `SECRET_KEY` in your environment and redeploy. Existing sessions
will be invalidated, which is the point.

### 2. Change the seeded admin password

`manage.py seed_data` used to create a superuser with a password written into
this repository, and the deployment section of the README told you to run it.
If you did, that account is a known email with a known password on your admin
panel.

```bash
python manage.py changepassword <the seeded admin email>
```

Or delete the account if you are not using it. The command now generates a
password instead, prints it once, and refuses to run with `DEBUG=False`.

### 3. Check `DEBUG`

`DEBUG` used to default to `True`. If your environment does not set it
explicitly, an older deployment is serving debug pages, which expose settings,
environment variables and stack traces to anyone who triggers an error. It
defaults to `False` now; set it explicitly either way.

## Getting the fixes

```bash
git remote add upstream https://github.com/eriktaveras/django-saas-boilerplate.git
git fetch upstream
git merge upstream/main
```

Beyond the three above, `main` also fixes a Stripe checkout that could not
complete on current API versions, a route that granted paid plans with no
payment, and a Content Security Policy that silently blocked 3-D Secure
challenges.
