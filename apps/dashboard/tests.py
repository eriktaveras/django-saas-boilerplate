from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import SubscriptionPlan, UserSettings

User = get_user_model()


class DashboardAccessTests(TestCase):
    def test_dashboard_redirects_anonymous(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_profile_redirects_anonymous(self):
        response = self.client.get('/dashboard/profile/')
        self.assertEqual(response.status_code, 302)

    def test_settings_redirects_anonymous(self):
        response = self.client.get('/dashboard/settings/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_accessible_when_logged_in(self):
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.client.force_login(user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)


class SubscriptionPlanModelTests(TestCase):
    def test_create_plan(self):
        plan = SubscriptionPlan.objects.create(
            name='Pro', slug='pro', description='Pro plan', price=9.99, interval='monthly', features=['API access'],
        )
        self.assertEqual(str(plan), 'Pro (Monthly)')
        self.assertTrue(plan.is_active)

    def test_user_settings_created_on_access(self):
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        settings, created = UserSettings.objects.get_or_create(user=user)
        self.assertTrue(created)
        self.assertEqual(settings.subscription_status, 'inactive')
