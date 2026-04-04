from django.test import TestCase


class LandingPageTests(TestCase):
    def test_home_page_returns_200(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_pricing_page_returns_200(self):
        response = self.client.get('/pricing/')
        self.assertEqual(response.status_code, 200)

    def test_features_page_returns_200(self):
        response = self.client.get('/features/')
        self.assertEqual(response.status_code, 200)

    def test_robots_txt_returns_200(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn('User-agent', response.content.decode())
