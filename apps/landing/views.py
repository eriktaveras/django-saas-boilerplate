from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET'])
def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        '',
        'Sitemap: https://yourdomain.com/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


@require_http_methods(['GET'])
def home(request):
    features = [
        {
            'icon': 'calendar-check',
            'title': 'Reserva en Línea',
            'description': 'Tus pacientes pueden reservar citas 24/7 a través de tu página personalizada. Sin llamadas telefónicas.',
        },
        {
            'icon': 'bell',
            'title': 'Recordatorios Inteligentes',
            'description': 'Los recordatorios automáticos por SMS y email reducen las inasistencias hasta en un 60%.',
        },
        {
            'icon': 'users',
            'title': 'Gestión de Pacientes',
            'description': 'Mantén un registro de tus pacientes, historial de visitas y preferencias en un solo lugar.',
        },
        {
            'icon': 'calendar',
            'title': 'Sincronización con Calendario',
            'description': 'Sincroniza con Google Calendar y Outlook. Tus citas siempre están actualizadas.',
        },
        {
            'icon': 'location-dot',
            'title': 'Multi-Ubicación',
            'description': 'Gestiona citas en múltiples ubicaciones de clínica desde un solo panel.',
        },
        {
            'icon': 'chart-line',
            'title': 'Panel de Análisis',
            'description': 'Rastrea tendencias de reservas, tasas de inasistencia y satisfacción de pacientes.',
        },
    ]

    return render(
        request,
        'landing/home.html',
        {
            'features': features,
        },
    )


@require_http_methods(['GET'])
def pricing(request):
    return render(request, 'landing/pricing.html')


@require_http_methods(['GET'])
def features(request):
    return render(request, 'landing/features.html')
