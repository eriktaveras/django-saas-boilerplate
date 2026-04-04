import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import StripeCustomer

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def subscription_page(request):
    try:
        # Get or create Stripe customer
        stripe_customer = StripeCustomer.objects.get(user=request.user)
        subscription = stripe.Subscription.retrieve(stripe_customer.stripe_subscription_id)
        return render(request, 'subscriptions/subscription.html', {
            'subscription': subscription,
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
        })
    except StripeCustomer.DoesNotExist:
        return render(request, 'subscriptions/subscription.html', {
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
        })

@login_required
def create_subscription(request):
    if request.method == 'POST':
        # Create or get Stripe customer
        try:
            stripe_customer = StripeCustomer.objects.get(user=request.user)
            customer = stripe_customer.stripe_customer_id
        except StripeCustomer.DoesNotExist:
            customer = stripe.Customer.create(
                email=request.user.email,
                source=request.POST['stripeToken']
            )
            stripe_customer = StripeCustomer.objects.create(
                user=request.user,
                stripe_customer_id=customer.id
            )

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer,
            items=[{'price': settings.STRIPE_PRICE_ID}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
        )

        stripe_customer.stripe_subscription_id = subscription.id
        stripe_customer.subscription_status = subscription.status
        stripe_customer.save()

        return JsonResponse({
            'subscription_id': subscription.id,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret,
        })

    return redirect('subscription_page')

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        stripe_customer = StripeCustomer.objects.get(stripe_subscription_id=subscription.id)
        stripe_customer.subscription_status = subscription.status
        stripe_customer.save()

    return HttpResponse(status=200)
