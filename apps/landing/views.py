from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET'])
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Sitemap: https://yourdomain.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


@require_http_methods(['GET'])
def home(request):
    features = [
        {
            'icon': 'shield-halved',
            'title': 'Authentication',
            'description': 'Email-based signup, login, verification, and password reset. Powered by django-allauth.',
        },
        {
            'icon': 'credit-card',
            'title': 'Stripe Payments',
            'description': 'Subscriptions, webhooks, and payment intents. Ready to accept payments on day one.',
        },
        {
            'icon': 'gauge-high',
            'title': 'Dashboard',
            'description': 'User profile, settings, notification preferences, and API key management built in.',
        },
        {
            'icon': 'bolt',
            'title': 'Background Tasks',
            'description': 'Django 6.0 native async tasks. No Celery, no Redis, no extra infrastructure.',
        },
        {
            'icon': 'lock',
            'title': 'Security',
            'description': 'CSP headers, HSTS, secure cookies, and SSL redirect. Production-grade from the start.',
        },
        {
            'icon': 'rocket',
            'title': 'Deploy Ready',
            'description': 'PostgreSQL, WhiteNoise, Gunicorn, and Procfile. Push to production in minutes.',
        },
    ]

    return render(request, 'landing/home.html', {
        'features': features,
    })


@require_http_methods(['GET'])
def pricing(request):
    return render(request, 'landing/pricing.html')


@require_http_methods(['GET'])
def features(request):
    return render(request, 'landing/features.html')
