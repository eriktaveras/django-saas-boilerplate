import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.dashboard.models import SubscriptionPlan

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with initial data. Development only.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-email',
            default=os.getenv('SEED_ADMIN_EMAIL', 'admin@example.com'),
            help='Email for the seeded superuser.',
        )

    def handle(self, *args, **options):
        # This creates a superuser. The command is documented in the README, so
        # it is easy to point at the wrong database; in a public repository any
        # fixed credential here is a published one, scannable across every
        # deployment that ran it.
        if not settings.DEBUG and os.getenv('ALLOW_SEED') != '1':
            raise CommandError(
                'seed_data creates a superuser and will not run with DEBUG=False. '
                'Set ALLOW_SEED=1 to override if you are certain this is not a '
                'production database.'
            )

        admin_email = options['admin_email']

        # Create admin user
        user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={'is_staff': True, 'is_superuser': True, 'first_name': 'Admin'},
        )
        if created:
            # Generated, never a literal: a password committed to a public repo
            # is a password everyone already has.
            password = os.getenv('SEED_ADMIN_PASSWORD') or secrets.token_urlsafe(16)
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Admin user created: {admin_email}'))
            self.stdout.write(self.style.WARNING(f'Password (shown once): {password}'))
        else:
            self.stdout.write('Admin user already exists')

        # Create subscription plans
        plans = [
            {
                'name': 'Free',
                'slug': 'free',
                'description': 'Get started with the basics',
                'price': 0,
                'interval': 'monthly',
                'features': ['Basic access', 'Community support', '1 project'],
            },
            {
                'name': 'Pro',
                'slug': 'pro',
                'description': 'For growing teams and businesses',
                'price': 9.99,
                'interval': 'monthly',
                'features': ['Everything in Free', 'Priority support', 'API access', '10 projects', 'Analytics'],
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'description': 'For large-scale operations',
                'price': 49.99,
                'interval': 'monthly',
                'features': [
                    'Everything in Pro',
                    'Dedicated support',
                    'Custom integrations',
                    'Unlimited projects',
                    'SLA guarantee',
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
