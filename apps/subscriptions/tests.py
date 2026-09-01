import json
from unittest.mock import patch

import stripe
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
