import hashlib
import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import SubscriptionPlan, UserSettings
from .tasks import (
    send_subscription_cancellation_email,
    send_subscription_confirmation_email,
    send_trial_started_email,
)


@login_required
@require_http_methods(['GET'])
def dashboard_home(request):
    return render(request, 'dashboard/home.html')

@login_required
@require_http_methods(['GET', 'POST'])
def profile(request):
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('dashboard:profile')
    return render(request, 'dashboard/profile.html')

@login_required
@require_http_methods(['GET', 'POST'])
def settings(request):
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_settings.notify_comments = request.POST.get('comments') == 'on'
        user_settings.notify_updates = request.POST.get('updates') == 'on'
        user_settings.notify_marketing = request.POST.get('marketing') == 'on'
        user_settings.save()

        messages.success(request, 'Settings updated successfully.')
        return redirect('dashboard:settings')

    # Check if a new API key was just generated (stored in session)
    new_api_key = request.session.pop('new_api_key', None)

    context = {
        'notification_settings': {
            'comments': user_settings.notify_comments,
            'updates': user_settings.notify_updates,
            'marketing': user_settings.notify_marketing,
        },
        'subscription': {
            'plan': user_settings.subscription_plan,
            'plan_name': user_settings.subscription_plan.name if user_settings.subscription_plan else None,
            'status': user_settings.subscription_status,
            'is_active': user_settings.is_subscription_active,
            'is_trial': user_settings.is_trial_active,
            'start_date': user_settings.subscription_start_date,
            'end_date': user_settings.subscription_end_date,
            'trial_end_date': user_settings.trial_end_date,
        },
        'api': {
            'has_key': bool(user_settings.api_key_hash),
            'key_prefix': user_settings.api_key_prefix,
            'key_created_at': user_settings.api_key_created_at,
            'new_key': new_api_key,
        },
    }
    return render(request, 'dashboard/settings.html', context)

@login_required
@require_http_methods(['POST'])
def generate_api_key(request):
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

    api_key = secrets.token_urlsafe(32)
    user_settings.api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    user_settings.api_key_prefix = api_key[:8]
    user_settings.api_key_created_at = timezone.now()
    user_settings.save()

    # Store the key in session so it can be shown once on the settings page
    request.session['new_api_key'] = api_key

    messages.success(request, 'API key generated. Copy it now — it won\'t be shown again.')
    return redirect('dashboard:settings')

@login_required
@require_http_methods(['GET'])
def subscription_plans(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

    context = {
        'plans': plans,
        'current_plan': user_settings.subscription_plan,
        'subscription_status': user_settings.subscription_status,
        'is_subscription_active': user_settings.is_subscription_active,
        'is_trial_active': user_settings.is_trial_active,
    }
    return render(request, 'dashboard/subscription_plans.html', context)

@login_required
@require_http_methods(['POST'])
def subscribe_to_plan(request, plan_slug):
    plan = get_object_or_404(SubscriptionPlan, slug=plan_slug, is_active=True)
    user_settings = UserSettings.objects.get(user=request.user)

    # Check if user already has an active subscription
    if user_settings.is_subscription_active:
        messages.warning(request, 'You already have an active subscription.')
        return redirect('dashboard:subscription_plans')

    # Update user settings with new subscription
    user_settings.subscription_plan = plan
    user_settings.subscription_status = 'active'
    user_settings.subscription_start_date = timezone.now()

    # Set subscription end date based on interval
    if plan.interval == 'monthly':
        user_settings.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
    else:  # yearly
        user_settings.subscription_end_date = timezone.now() + timezone.timedelta(days=365)

    user_settings.save()

    send_subscription_confirmation_email.enqueue(
        user_email=request.user.email,
        plan_name=plan.name,
    )

    messages.success(request, f'Successfully subscribed to {plan.name} plan.')
    return redirect('dashboard:settings')

@login_required
@require_http_methods(['POST'])
def cancel_subscription(request):
    user_settings = UserSettings.objects.get(user=request.user)

    if not user_settings.is_subscription_active:
        messages.warning(request, 'You do not have an active subscription to cancel.')
        return redirect('dashboard:settings')

    user_settings.subscription_status = 'cancelled'
    user_settings.save()

    send_subscription_cancellation_email.enqueue(user_email=request.user.email)

    messages.success(request, 'Your subscription has been cancelled.')
    return redirect('dashboard:settings')

@login_required
@require_http_methods(['POST'])
def start_trial(request):
    user_settings = UserSettings.objects.get(user=request.user)

    if user_settings.is_subscription_active or user_settings.is_trial_active:
        messages.warning(request, 'You already have an active subscription or trial.')
        return redirect('dashboard:subscription_plans')

    # Start trial period (14 days)
    user_settings.subscription_status = 'trial'
    user_settings.trial_end_date = timezone.now() + timezone.timedelta(days=14)
    user_settings.save()

    send_trial_started_email.enqueue(user_email=request.user.email)

    messages.success(request, 'Trial period started successfully.')
    return redirect('dashboard:settings')
