# Stripe subscriptions

Checkout uses Stripe's Payment Methods API, Stripe SDK 15.x and the API version
configured in `core/settings.py`. This module supports a single configured
recurring price; dashboard plans are not automatically mapped to Stripe prices.

## Setup

Install the root `requirements.txt` with Python 3.12+ and configure `.env`:

```env
DEBUG=True
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
```

Use a recurring Stripe price. Configure your signed webhook endpoint at
`https://your-domain.com/subscriptions/webhook/` for exactly these supported events:

- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

Production also requires `SECRET_KEY` with debug disabled and working SMTP
settings for email delivery. See the [root README](../../README.md) for setup.

## Checkout and access

Authenticated users visit `/subscriptions/`. The browser creates a PaymentMethod
with Stripe.js and POSTs JSON containing `payment_method_id` to
`/subscriptions/create/`. The server strips surrounding whitespace and rejects
invalid JSON, non-object bodies, missing or blank payment methods, and a missing
configured price with HTTP 400 before calling Stripe.

Checkout reuses an existing Stripe customer, attaches the PaymentMethod, sets it
as the invoice default, and creates a subscription using `default_incomplete`.
An idempotency key includes the user, configured price, and payment method.
The response includes `subscription_id`, `client_secret`,
`requires_confirmation`, and `status`. The secret comes from
`latest_invoice.confirmation_secret`; trials or zero-cost invoices can return
no secret. Card declines return 402; other Stripe errors return 502.

`StripeCustomer` stores customer/subscription identifiers and Stripe status.
`_sync_access` in `views.py` mirrors status and available period/trial dates into
`apps.dashboard.models.UserSettings`, creating the row when needed:

| Stripe status | Local status |
| --- | --- |
| `active`, `past_due` | `active` |
| `trialing` | `trial` |
| `canceled` | `cancelled` |
| `unpaid`, `incomplete`, `incomplete_expired`, `paused`, unknown | `inactive` |

Dashboard access also checks local expiry dates. The period end comes from the
first subscription item's `current_period_end`. Missing dates leave stored dates
unchanged, preserving the marker that a trial has already been used.

## Webhook behavior

The endpoint accepts POST only and verifies the raw body with the Stripe
signature and `STRIPE_WEBHOOK_SECRET`. Invalid payloads/signatures return 400;
a missing signing secret returns 500. The webhook is CSRF-exempt; checkout uses
normal Django CSRF protection and requires login.

Updates and deletions synchronize only a matching stored subscription ID.
A `created` event can link a customer with an empty subscription ID only if its
items include `STRIPE_PRICE_ID`. Once linked, `created` events are acknowledged
without changing status or dates, so a delayed initial snapshot cannot overwrite
checkout, updates or cancellation. Unknown subscriptions, irrelevant prices and
unsupported event types are acknowledged with 200 without changing access.

There are no `invoice.payment_succeeded` or `invoice.payment_failed` handlers,
failed-payment recovery, customer portal, or invoice history. General ordering
protection for delayed `updated`/`deleted` events is not implemented.

## Dashboard actions and email tasks

Direct free-plan subscription and trial actions create missing `UserSettings`;
users do not have to visit settings first. Paid dashboard plans redirect to
Stripe checkout. The local trial lasts 14 days, rejects active subscriptions or
trials, and cannot be repeated once `trial_end_date` is set.

Paid cancellation calls Stripe with `cancel_at_period_end=True` and retains
local access until expiry or subsequent webhook synchronization. Stripe errors
leave the subscription unchanged. Without a linked Stripe subscription, local
active subscriptions are cancelled immediately.

Free-plan activation, local cancellation and trial-start emails use the `@task`
functions in `apps/dashboard/tasks.py`. Stripe checkout does not send a confirmation
email. `ImmediateBackend` runs `.enqueue()` immediately
in the calling process. No asynchronous worker or durable queue is configured.

## Files and validation

- `models.py`: `StripeCustomer`.
- `views.py`: `subscription_page`, `create_subscription`, `stripe_webhook`, and synchronization helpers.
- `urls.py`: namespaced subscription routes.
- `../../templates/subscriptions/subscription.html`: checkout UI.
- `../dashboard/models.py`: `SubscriptionPlan` and `UserSettings`.
- `../dashboard/views.py`: free plans, trials and cancellation.

Run from the repository root:

```bash
DEBUG=True venv/bin/python manage.py test
DEBUG=True venv/bin/python manage.py check
DEBUG=True venv/bin/python manage.py makemigrations --check --dry-run
venv/bin/ruff check .
```

See [root README: Local validation](../../README.md#local-validation) for the test count and breakdown.
Stripe calls are mocked; tests do not require live Stripe access. Validation is
local, with no CI workflows configured.
