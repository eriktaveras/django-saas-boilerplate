import json
import logging
from datetime import datetime
from datetime import timezone as dt_timezone

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import StripeCustomer

stripe.api_key = settings.STRIPE_SECRET_KEY
# Pinned on purpose rather than inherited from the installed SDK.
# See STRIPE_API_VERSION in core/settings.py.
stripe.api_version = settings.STRIPE_API_VERSION

logger = logging.getLogger(__name__)

@login_required
def subscription_page(request):
    subscription = None
    stripe_customer = StripeCustomer.objects.filter(user=request.user).first()

    if stripe_customer and stripe_customer.stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(stripe_customer.stripe_subscription_id)
        except stripe.StripeError:
            # A subscription id Stripe no longer knows about (deleted in the
            # dashboard, or created with test keys) must not 500 the page.
            logger.exception('Could not load subscription for user %s', request.user.pk)
            subscription = None

    return render(request, 'subscriptions/subscription.html', {
        'subscription': subscription,
        'current_period_end': _current_period_end(subscription),
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
    })


def _current_period_end(subscription):
    """Renewal date of a subscription, as a datetime.

    Two things make this less obvious than it looks. The period moved off the
    subscription onto each subscription item, and Stripe sends it as a Unix
    timestamp, which Django's `date` filter renders as an empty string.
    """
    if subscription is None:
        return None

    items = getattr(subscription, 'items', None)
    data = getattr(items, 'data', None) or []
    timestamp = getattr(data[0], 'current_period_end', None) if data else None
    if timestamp is None:
        return None

    return datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)

@login_required
@require_POST
def create_subscription(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    payment_method_id = data.get('payment_method_id')
    if not payment_method_id:
        return JsonResponse({'error': 'Payment method is required'}, status=400)

    if not settings.STRIPE_PRICE_ID:
        return JsonResponse({'error': 'No Stripe price configured'}, status=400)

    try:
        stripe_customer = StripeCustomer.objects.filter(user=request.user).first()
        if stripe_customer and stripe_customer.stripe_customer_id:
            customer_id = stripe_customer.stripe_customer_id
        else:
            customer = stripe.Customer.create(email=request.user.email)
            customer_id = customer.id
            stripe_customer, _ = StripeCustomer.objects.update_or_create(
                user=request.user,
                defaults={'stripe_customer_id': customer_id},
            )

        # The card reaches Stripe as a PaymentMethod (created in the browser by
        # stripe.js), never as a legacy token, and it has to be attached to the
        # customer before the subscription can charge it.
        stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        stripe.Customer.modify(
            customer_id,
            invoice_settings={'default_payment_method': payment_method_id},
        )

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': settings.STRIPE_PRICE_ID}],
            payment_behavior='default_incomplete',
            # `latest_invoice.payment_intent` was removed from the API. The
            # secret the browser confirms with now lives on the invoice's
            # confirmation_secret.
            expand=['latest_invoice.confirmation_secret'],
            # A double-clicked button must not create two paid subscriptions:
            # Stripe replays the first result instead.
            idempotency_key=f'sub:{request.user.pk}:{settings.STRIPE_PRICE_ID}:{payment_method_id}',
        )
    except stripe.CardError as exc:
        return JsonResponse({'error': exc.user_message or 'Your card was declined.'}, status=402)
    except stripe.StripeError:
        logger.exception('Stripe rejected the subscription for user %s', request.user.pk)
        return JsonResponse(
            {'error': 'We could not start your subscription. Please try again.'},
            status=502,
        )

    stripe_customer.stripe_subscription_id = subscription.id
    stripe_customer.subscription_status = subscription.status
    stripe_customer.save()

    # Attribute access, not .get(): a Stripe resource object is not a dict.
    # If the expand above ever stops resolving, latest_invoice comes back as a
    # bare id string and these fall through to None instead of raising.
    invoice = getattr(subscription, 'latest_invoice', None)
    confirmation_secret = getattr(invoice, 'confirmation_secret', None)
    client_secret = getattr(confirmation_secret, 'client_secret', None)

    return JsonResponse({
        'subscription_id': subscription.id,
        'client_secret': client_secret,
        # A trial or a 100% coupon leaves nothing for the browser to confirm.
        'requires_confirmation': bool(client_secret),
        'status': subscription.status,
    })

@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        # Without a secret nothing is verifiable, so anyone could post a fake
        # "subscription active". Refuse rather than trust the payload.
        logger.error('STRIPE_WEBHOOK_SECRET is not set; refusing to process webhooks')
        return HttpResponse(status=500)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] in ('customer.subscription.updated', 'customer.subscription.deleted'):
        subscription = event['data']['object']
        stripe_customer = StripeCustomer.objects.filter(
            stripe_subscription_id=subscription['id']
        ).first()
        if stripe_customer is None:
            # Unknown subscription. Acknowledge it, or Stripe retries forever.
            logger.warning('Webhook: no StripeCustomer for subscription %s', subscription['id'])
            return HttpResponse(status=200)

        stripe_customer.subscription_status = subscription['status']
        stripe_customer.save()

    return HttpResponse(status=200)
