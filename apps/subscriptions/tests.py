import json
from unittest.mock import patch

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import StripeCustomer

User = get_user_model()


@override_settings(STRIPE_PRICE_ID='price_123', STRIPE_WEBHOOK_SECRET='whsec_x')
class CheckoutSmokeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='a@example.com', password='pw12345678')
        self.client.force_login(self.user)

    @patch('apps.subscriptions.views.stripe.Subscription.create')
    @patch('apps.subscriptions.views.stripe.Customer.modify')
    @patch('apps.subscriptions.views.stripe.PaymentMethod.attach')
    @patch('apps.subscriptions.views.stripe.Customer.create')
    def test_returns_confirmation_secret(self, cust_create, pm_attach, cust_mod, sub_create):
        cust_create.return_value = stripe.Customer.construct_from({'id': 'cus_1'}, 'k')
        sub_create.return_value = stripe.Subscription.construct_from({
            'id': 'sub_1',
            'status': 'incomplete',
            'latest_invoice': {
                'id': 'in_1',
                'confirmation_secret': {'client_secret': 'pi_1_secret_abc', 'type': 'payment_intent'},
            },
        }, 'k')

        resp = self.client.post(
            reverse('subscriptions:create_subscription'),
            data=json.dumps({'payment_method_id': 'pm_1'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body['client_secret'], 'pi_1_secret_abc')
        self.assertTrue(body['requires_confirmation'])
        self.assertEqual(body['status'], 'incomplete')

        kwargs = sub_create.call_args.kwargs
        self.assertEqual(kwargs['expand'], ['latest_invoice.confirmation_secret'])
        self.assertIn('idempotency_key', kwargs)

        sc = StripeCustomer.objects.get(user=self.user)
        self.assertEqual(sc.stripe_subscription_id, 'sub_1')

    @patch('apps.subscriptions.views.stripe.Customer.create')
    def test_card_error_is_402(self, cust_create):
        cust_create.side_effect = stripe.CardError('declined', None, 'card_declined')
        resp = self.client.post(
            reverse('subscriptions:create_subscription'),
            data=json.dumps({'payment_method_id': 'pm_1'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 402)
        self.assertIn('error', resp.json())

    @patch('apps.subscriptions.views.stripe.Customer.create')
    def test_stripe_error_is_502(self, cust_create):
        cust_create.side_effect = stripe.APIConnectionError('boom')
        resp = self.client.post(
            reverse('subscriptions:create_subscription'),
            data=json.dumps({'payment_method_id': 'pm_1'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 502)

    def test_bad_signature_returns_400_not_500(self):
        resp = self.client.post(
            reverse('subscriptions:stripe_webhook'),
            data='{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=bogus',
        )
        self.assertEqual(resp.status_code, 400)

    @patch('apps.subscriptions.views.stripe.Webhook.construct_event')
    def test_webhook_updates_status(self, construct):
        StripeCustomer.objects.create(
            user=self.user, stripe_customer_id='cus_1', stripe_subscription_id='sub_1'
        )
        construct.return_value = {
            'id': 'evt_1',
            'type': 'customer.subscription.updated',
            'data': {'object': {'id': 'sub_1', 'status': 'active'}},
        }
        resp = self.client.post(
            reverse('subscriptions:stripe_webhook'),
            data='{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='sig',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(StripeCustomer.objects.get(user=self.user).subscription_status, 'active')

    @patch('apps.subscriptions.views.stripe.Webhook.construct_event')
    def test_webhook_unknown_subscription_is_200(self, construct):
        construct.return_value = {
            'id': 'evt_2',
            'type': 'customer.subscription.updated',
            'data': {'object': {'id': 'sub_unknown', 'status': 'active'}},
        }
        resp = self.client.post(
            reverse('subscriptions:stripe_webhook'),
            data='{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='sig',
        )
        self.assertEqual(resp.status_code, 200)

    def test_subscription_page_without_customer(self):
        resp = self.client.get(reverse('subscriptions:subscription_page'))
        self.assertEqual(resp.status_code, 200)

    def test_subscription_page_with_blank_subscription_id(self):
        StripeCustomer.objects.create(user=self.user, stripe_customer_id='cus_1')
        resp = self.client.get(reverse('subscriptions:subscription_page'))
        self.assertEqual(resp.status_code, 200)


class CurrentPeriodEndTest(TestCase):
    def test_reads_the_date_off_the_subscription_item(self):
        from apps.subscriptions.views import _current_period_end

        sub = stripe.Subscription.construct_from({
            'id': 'sub_1',
            'status': 'active',
            'items': {'object': 'list', 'data': [{'id': 'si_1', 'current_period_end': 1767225600}]},
        }, 'k')
        self.assertEqual(_current_period_end(sub).year, 2026)

    def test_missing_period_is_none_not_an_error(self):
        from apps.subscriptions.views import _current_period_end

        self.assertIsNone(_current_period_end(None))
        sub = stripe.Subscription.construct_from({'id': 'sub_1', 'status': 'active'}, 'k')
        self.assertIsNone(_current_period_end(sub))


class SettingsHardeningTest(TestCase):
    """This repository is public, so a committed default is a published value.

    These pin the failure direction: a deployment that forgets a variable must
    stop, not quietly run with something everyone can read.
    """

    def test_no_hardcoded_secret_key_fallback(self):
        import pathlib
        import re

        settings_src = (pathlib.Path(__file__).resolve().parents[2] / "core" / "settings.py").read_text()
        assignment = re.search(r"^SECRET_KEY = .*$", settings_src, re.M).group(0)

        # A fallback here ships a key that anyone can read off GitHub and use to
        # forge session cookies on every deployment that forgot the variable.
        self.assertNotIn("django-insecure-default", assignment)
        self.assertEqual(assignment, "SECRET_KEY = os.getenv('SECRET_KEY')")

    def test_debug_fails_closed(self):
        import pathlib
        import re

        settings_src = (pathlib.Path(__file__).resolve().parents[2] / "core" / "settings.py").read_text()
        assignment = re.search(r"^DEBUG = os\.getenv.*$", settings_src, re.M).group(0)

        self.assertIn("'DEBUG', 'False'", assignment)

    def test_the_proxy_header_is_set(self):
        # Without it, SECURE_SSL_REDIRECT loops forever behind a PaaS edge and
        # HSTS is never emitted.
        self.assertEqual(
            settings.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https")
        )

    def test_email_does_not_default_to_console_in_production(self):
        import pathlib

        settings_src = (pathlib.Path(__file__).resolve().parents[2] / "core" / "settings.py").read_text()

        # Verification links printed to a production log reach nobody.
        self.assertIn("if DEBUG", settings_src.split("EMAIL_BACKEND = os.getenv(")[1][:200])


class PaidPlanCannotBeSelfGrantedTest(TestCase):
    """subscribe_to_plan activates a plan with no payment step, so a POST to it
    used to hand any signed-in user a paid tier for free. In a boilerplate whose
    whole point is billing, that is the most expensive bug it can have."""

    def setUp(self):
        from apps.dashboard.models import SubscriptionPlan, UserSettings

        self.user = User.objects.create_user(email="freeloader@example.com", password="testpass123")
        UserSettings.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)
        self.paid = SubscriptionPlan.objects.create(
            name="Enterprise", slug="enterprise", price=49.99, interval="monthly", is_active=True
        )
        self.free = SubscriptionPlan.objects.create(
            name="Free", slug="free", price=0, interval="monthly", is_active=True
        )

    def _subscribe(self, slug):
        return self.client.post(f"/dashboard/subscription/plans/{slug}/subscribe/")

    def _settings(self):
        from apps.dashboard.models import UserSettings

        return UserSettings.objects.get(user=self.user)

    def test_a_paid_plan_cannot_be_granted_without_paying(self):
        self._subscribe("enterprise")

        settings_row = self._settings()
        self.assertNotEqual(settings_row.subscription_status, "active")
        self.assertIsNone(settings_row.subscription_plan)

    def test_a_free_plan_still_activates(self):
        self._subscribe("free")

        settings_row = self._settings()
        self.assertEqual(settings_row.subscription_status, "active")
        self.assertEqual(settings_row.subscription_plan, self.free)

    def test_the_free_trial_cannot_be_restarted_once_used(self):
        from django.utils import timezone

        # An expired trial leaves trial_end_date behind but makes both the
        # active checks False, which is how it used to become repeatable.
        row = self._settings()
        row.trial_end_date = timezone.now() - timezone.timedelta(days=1)
        row.save()

        self.client.post("/dashboard/subscription/trial/")

        row.refresh_from_db()
        self.assertLess(row.trial_end_date, timezone.now())


class SeedDataGuardTest(TestCase):
    """The README documents this command, including in its deployment section,
    so it must not be able to fire against a production database."""

    def test_it_refuses_to_run_with_debug_off(self):
        from io import StringIO

        from django.core.management import call_command
        from django.core.management.base import CommandError

        with override_settings(DEBUG=False):
            with self.assertRaises(CommandError):
                call_command("seed_data", stdout=StringIO())

    def test_no_password_literal_survives_in_the_command(self):
        import pathlib

        src = (
            pathlib.Path(__file__).resolve().parents[2]
            / "apps" / "dashboard" / "management" / "commands" / "seed_data.py"
        ).read_text()

        self.assertNotIn("admin123", src)


class PaidAccessIsGrantedTest(TestCase):
    """Two subscription records live side by side: StripeCustomer, written by
    the payment flow, and UserSettings, read by every permission check. Nothing
    connected them, so a customer could pay, have Stripe report the
    subscription active, and still be locked out of what they just bought."""

    def setUp(self):
        from apps.dashboard.models import UserSettings

        self.user = User.objects.create_user(email="payer@example.com", password="testpass123")
        UserSettings.objects.get_or_create(user=self.user)

    def _settings(self):
        from apps.dashboard.models import UserSettings

        return UserSettings.objects.get(user=self.user)

    def test_an_active_stripe_status_grants_access(self):
        from .views import _sync_access

        _sync_access(self.user, "active")

        self.assertTrue(self._settings().is_subscription_active)

    def test_a_trialing_status_grants_trial_access(self):
        from .views import _sync_access

        _sync_access(self.user, "trialing")

        self.assertTrue(self._settings().is_trial_active)

    def test_past_due_keeps_access_while_stripe_retries(self):
        from .views import _sync_access

        _sync_access(self.user, "past_due")

        self.assertTrue(self._settings().is_subscription_active)

    def test_an_incomplete_payment_grants_nothing(self):
        from .views import _sync_access

        _sync_access(self.user, "incomplete")

        self.assertFalse(self._settings().is_subscription_active)

    def test_a_cancelled_subscription_revokes_access(self):
        from .views import _sync_access

        _sync_access(self.user, "active")
        _sync_access(self.user, "canceled")

        self.assertFalse(self._settings().is_subscription_active)

    def test_an_unknown_status_denies_rather_than_grants(self):
        from .views import _sync_access

        _sync_access(self.user, "something_stripe_added_last_week")

        self.assertFalse(self._settings().is_subscription_active)


class CancelReachesStripeTest(TestCase):
    """Cancelling used to flip a local flag and nothing else, so Stripe kept
    charging the card every month for a subscription the customer believed they
    had cancelled."""

    def setUp(self):
        from apps.dashboard.models import UserSettings

        self.user = User.objects.create_user(email="quitter@example.com", password="testpass123")
        UserSettings.objects.get_or_create(user=self.user)
        StripeCustomer.objects.create(
            user=self.user, stripe_customer_id="cus_1", stripe_subscription_id="sub_1"
        )
        self.client.force_login(self.user)

    @patch("apps.dashboard.views.stripe")
    def test_it_cancels_at_stripe(self, mock_stripe):
        mock_stripe.StripeError = Exception

        self.client.post("/dashboard/subscription/cancel/")

        mock_stripe.Subscription.modify.assert_called_once_with(
            "sub_1", cancel_at_period_end=True
        )

    @patch("apps.dashboard.views.stripe")
    def test_a_stripe_failure_does_not_pretend_it_cancelled(self, mock_stripe):
        # Telling someone their subscription is cancelled when it is not is how
        # a chargeback starts.
        mock_stripe.StripeError = Exception
        mock_stripe.Subscription.modify.side_effect = Exception("network")

        response = self.client.post("/dashboard/subscription/cancel/", follow=True)

        self.assertContains(response, "was not")
