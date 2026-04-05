from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from apps.dashboard.models import SubscriptionPlan

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with initial data (admin user + subscription plans + site config)'

    def handle(self, *args, **options):
        # Configure site domain
        site = Site.objects.get_or_create(id=settings.SITE_ID)[0]
        site.domain = settings.SITE_DOMAIN
        site.name = 'MediBook'
        site.save()
        self.stdout.write(self.style.SUCCESS(f'Site configured: {site.domain}'))

        # Create admin user
        user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={'is_staff': True, 'is_superuser': True, 'first_name': 'Admin'},
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Admin user created (admin@example.com / admin123)'))
        else:
            self.stdout.write('Admin user already exists')

        # Create subscription plans
        plans = [
            {
                'name': 'Básico',
                'slug': 'starter',
                'description': 'Perfecto para clínicas pequeñas que apenas comienzan',
                'price': 29,
                'interval': 'monthly',
                'features': ['1 ubicación', '100 citas/mes', 'Recordatorios por email', 'Panel básico'],
            },
            {
                'name': 'Profesional',
                'slug': 'professional',
                'description': 'Para consultorios en crecimiento que necesitan más',
                'price': 79,
                'interval': 'monthly',
                'features': [
                    '3 ubicaciones',
                    '500 citas/mes',
                    'SMS + recordatorios por email',
                    'Sincronización con calendario',
                    'Análisis',
                ],
            },
            {
                'name': 'Empresarial',
                'slug': 'enterprise',
                'description': 'Para grandes consultorios y grupos médicos',
                'price': 199,
                'interval': 'monthly',
                'features': [
                    'Ubicaciones ilimitadas',
                    'Citas ilimitadas',
                    'Acceso a API',
                    'Integraciones personalizadas',
                    'Soporte prioritario',
                ],
            },
        ]

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                slug=plan_data['slug'],
                defaults=plan_data,
            )
            status = 'created' if created else 'already exists'
            self.stdout.write(self.style.SUCCESS(f'Plan "{plan.name}" {status}'))

        self.stdout.write(self.style.SUCCESS('\nSeed data complete!'))
