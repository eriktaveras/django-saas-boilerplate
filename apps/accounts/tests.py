from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class CustomUserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.assertEqual(user.email, 'test@example.com')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('testpass123'))

    def test_create_superuser(self):
        user = User.objects.create_superuser(email='admin@example.com', password='admin123')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')

    def test_user_str_returns_email(self):
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        self.assertEqual(str(user), 'test@example.com')

    def test_signup_page_returns_200(self):
        response = self.client.get('/accounts/signup/')
        self.assertEqual(response.status_code, 200)

    def test_login_page_returns_200(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)
