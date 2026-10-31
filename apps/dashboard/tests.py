import hashlib
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

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


class ApiKeyHashingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.client.force_login(self.user)

    def test_generate_api_key_stores_only_hash(self):
        self.client.post(reverse('dashboard:generate_api_key'))
        settings = UserSettings.objects.get(user=self.user)
        plaintext = self.client.session['new_api_key']

        self.assertEqual(len(settings.api_key_hash), 64)
        self.assertNotEqual(settings.api_key_hash, plaintext)
        self.assertEqual(settings.api_key_hash, hashlib.sha256(plaintext.encode()).hexdigest())

    def test_api_key_prefix_stored_for_display(self):
        self.client.post(reverse('dashboard:generate_api_key'))
        settings = UserSettings.objects.get(user=self.user)
        plaintext = self.client.session['new_api_key']

        self.assertEqual(settings.api_key_prefix, plaintext[:8])

    def test_regenerating_key_replaces_hash(self):
        self.client.post(reverse('dashboard:generate_api_key'))
        first_hash = UserSettings.objects.get(user=self.user).api_key_hash

        self.client.post(reverse('dashboard:generate_api_key'))
        second_hash = UserSettings.objects.get(user=self.user).api_key_hash

        self.assertNotEqual(first_hash, second_hash)


class SubscriptionActionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='new@example.com', password='testpass123')
        self.client.force_login(self.user)
        self.free_plan = SubscriptionPlan.objects.create(name='Free', slug='free', price=0)
        self.now = timezone.now()
        clock = patch('apps.dashboard.views.timezone.now', return_value=self.now)
        clock.start()
        self.addCleanup(clock.stop)
        self.emails = {}
        for name in ('subscription_confirmation', 'trial_started', 'subscription_cancellation'):
            mock = patch(f'apps.dashboard.views.send_{name}_email.enqueue')
            self.emails[name] = mock.start()
            self.addCleanup(mock.stop)

    def subscribe(self, plan=None):
        return self.client.post(reverse('dashboard:subscribe_to_plan', args=[(plan or self.free_plan).slug]))

    def test_direct_free_subscription_creates_settings(self):
        self.assertFalse(UserSettings.objects.filter(user=self.user).exists())
        response = self.subscribe()
        self.assertRedirects(response, reverse('dashboard:settings'), fetch_redirect_response=False)
        settings = UserSettings.objects.get(user=self.user)
        self.assertEqual(settings.subscription_plan, self.free_plan)
        self.assertEqual(settings.subscription_status, 'active')
        self.assertEqual(settings.subscription_start_date, self.now)
        self.assertEqual(settings.subscription_end_date, self.now + timezone.timedelta(days=30))
        self.emails['subscription_confirmation'].assert_called_once_with(
            user_email=self.user.email, plan_name=self.free_plan.name,
        )

    def test_direct_yearly_free_subscription(self):
        self.free_plan.interval = 'yearly'
        self.free_plan.save()
        self.subscribe()
        settings = UserSettings.objects.get(user=self.user)
        self.assertEqual(settings.subscription_end_date, self.now + timezone.timedelta(days=365))

    def test_direct_paid_subscription_requires_checkout(self):
        for interval in ('monthly', 'yearly'):
            with self.subTest(interval=interval):
                plan = SubscriptionPlan.objects.create(
                    name='Paid', slug=f'paid-{interval}', price='9.99', interval=interval,
                )
                response = self.subscribe(plan)
                self.assertRedirects(
                    response, reverse('subscriptions:subscription_page'), fetch_redirect_response=False,
                )
                settings = UserSettings.objects.get(user=self.user)
                self.assertEqual(settings.subscription_status, 'inactive')
                self.assertIsNone(settings.subscription_plan)
                self.assertIsNone(settings.subscription_start_date)
                self.assertIsNone(settings.subscription_end_date)
                settings.delete()
        self.emails['subscription_confirmation'].assert_not_called()

    def test_inactive_plan_cannot_be_subscribed(self):
        self.free_plan.is_active = False
        self.free_plan.save()
        self.assertEqual(self.subscribe().status_code, 404)
        self.assertFalse(UserSettings.objects.filter(user=self.user).exists())
        self.emails['subscription_confirmation'].assert_not_called()

    def test_active_subscription_cannot_be_replaced(self):
        paid_plan = SubscriptionPlan.objects.create(name='Paid', slug='paid', price='9.99')
        settings = UserSettings.objects.create(
            user=self.user, subscription_plan=paid_plan, subscription_status='active',
            subscription_end_date=self.now + timezone.timedelta(days=10),
        )
        response = self.subscribe()
        self.assertRedirects(response, reverse('dashboard:subscription_plans'), fetch_redirect_response=False)
        settings.refresh_from_db()
        self.assertEqual(settings.subscription_plan, paid_plan)
        self.assertEqual(settings.subscription_end_date, self.now + timezone.timedelta(days=10))
        self.emails['subscription_confirmation'].assert_not_called()

    def test_direct_trial_creates_settings(self):
        self.assertFalse(UserSettings.objects.filter(user=self.user).exists())
        response = self.client.post(reverse('dashboard:start_trial'))
        self.assertRedirects(response, reverse('dashboard:settings'), fetch_redirect_response=False)
        settings = UserSettings.objects.get(user=self.user)
        self.assertEqual(settings.subscription_status, 'trial')
        self.assertEqual(settings.trial_end_date, self.now + timezone.timedelta(days=14))
        self.assertTrue(settings.is_trial_active)
        self.emails['trial_started'].assert_called_once_with(user_email=self.user.email)

    def test_trial_cannot_replace_active_subscription_or_trial(self):
        for status in ('active', 'trial'):
            with self.subTest(status=status):
                settings = UserSettings.objects.create(
                    user=self.user, subscription_status=status,
                    trial_end_date=self.now + timezone.timedelta(days=7),
                )
                response = self.client.post(reverse('dashboard:start_trial'))
                self.assertRedirects(response, reverse('dashboard:subscription_plans'), fetch_redirect_response=False)
                settings.refresh_from_db()
                self.assertEqual(settings.subscription_status, status)
                self.assertEqual(settings.trial_end_date, self.now + timezone.timedelta(days=7))
                settings.delete()
        self.emails['trial_started'].assert_not_called()

    def test_used_trial_cannot_be_restarted(self):
        for status in ('trial', 'inactive', 'cancelled'):
            with self.subTest(status=status):
                settings = UserSettings.objects.create(
                    user=self.user, subscription_status=status,
                    trial_end_date=self.now - timezone.timedelta(days=1),
                )
                response = self.client.post(reverse('dashboard:start_trial'))
                self.assertRedirects(response, reverse('dashboard:subscription_plans'), fetch_redirect_response=False)
                settings.refresh_from_db()
                self.assertEqual(settings.subscription_status, status)
                self.assertEqual(settings.trial_end_date, self.now - timezone.timedelta(days=1))
                settings.delete()
        self.emails['trial_started'].assert_not_called()

    def test_direct_cancellation_without_subscription_creates_settings(self):
        response = self.client.post(reverse('dashboard:cancel_subscription'))
        self.assertRedirects(response, reverse('dashboard:settings'), fetch_redirect_response=False)
        settings = UserSettings.objects.get(user=self.user)
        self.assertEqual(settings.subscription_status, 'inactive')
        self.emails['subscription_cancellation'].assert_not_called()

    def test_free_subscription_can_be_cancelled_only_once(self):
        self.subscribe()
        for _ in range(2):
            response = self.client.post(reverse('dashboard:cancel_subscription'))
            self.assertRedirects(response, reverse('dashboard:settings'), fetch_redirect_response=False)
        settings = UserSettings.objects.get(user=self.user)
        self.assertEqual(settings.subscription_status, 'cancelled')
        self.assertFalse(settings.is_subscription_active)
        self.emails['subscription_cancellation'].assert_called_once_with(user_email=self.user.email)

    def test_trial_and_expired_subscription_cannot_be_cancelled(self):
        for status in ('trial', 'active'):
            with self.subTest(status=status):
                settings = UserSettings.objects.create(
                    user=self.user, subscription_status=status,
                    subscription_end_date=self.now - timezone.timedelta(days=1),
                    trial_end_date=self.now + timezone.timedelta(days=7),
                )
                response = self.client.post(reverse('dashboard:cancel_subscription'))
                self.assertRedirects(response, reverse('dashboard:settings'), fetch_redirect_response=False)
                settings.refresh_from_db()
                self.assertEqual(settings.subscription_status, status)
                settings.delete()
        self.emails['subscription_cancellation'].assert_not_called()

    def test_subscription_actions_require_login_and_post(self):
        urls = [
            reverse('dashboard:subscribe_to_plan', args=[self.free_plan.slug]),
            reverse('dashboard:start_trial'),
            reverse('dashboard:cancel_subscription'),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)
        self.client.logout()
        for url in urls:
            with self.subTest(url=url):
                response = self.client.post(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('account_login')))
        self.assertFalse(UserSettings.objects.filter(user=self.user).exists())
