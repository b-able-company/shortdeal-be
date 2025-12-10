"""
Tests for password reset functionality
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from .models import User


class PasswordResetAPITestCase(TestCase):
    """Test password reset API endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123',
            role=User.Role.BUYER,
            is_active=True
        )

    def test_password_reset_request_success(self):
        """Test successful password reset request"""
        url = reverse('accounts_api:password_reset_request')
        data = {'email': 'test@example.com'}

        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Reset Your Password', mail.outbox[0].subject)

    def test_password_reset_request_case_insensitive(self):
        """Test password reset with case-insensitive email"""
        url = reverse('accounts_api:password_reset_request')
        data = {'email': 'TEST@example.com'}

        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_request_nonexistent_email(self):
        """Test password reset with non-existent email (no user enumeration)"""
        url = reverse('accounts_api:password_reset_request')
        data = {'email': 'nonexistent@example.com'}

        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        # Should still return 200 to prevent user enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        # But no email should be sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_request_invalid_email(self):
        """Test password reset with invalid email format"""
        url = reverse('accounts_api:password_reset_request')
        data = {'email': 'notanemail'}

        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_password_reset_confirm_success(self):
        """Test successful password reset confirmation"""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        url = reverse('accounts_api:password_reset_confirm')
        data = {
            'uid': uid,
            'token': token,
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }

        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['success'])
        self.assertIn('tokens', response.json()['data'])

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

    def test_password_reset_confirm_password_mismatch(self):
        """Test password reset with mismatched passwords"""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        url = reverse('accounts_api:password_reset_confirm')
        data = {
            'uid': uid,
            'token': token,
            'new_password': 'newpassword123',
            'new_password_confirm': 'differentpassword123'
        }

        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_password_reset_confirm_weak_password(self):
        """Test password reset with weak password"""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        url = reverse('accounts_api:password_reset_confirm')
        data = {
            'uid': uid,
            'token': token,
            'new_password': '123',
            'new_password_confirm': '123'
        }

        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_password_reset_confirm_invalid_token(self):
        """Test password reset with invalid token"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        url = reverse('accounts_api:password_reset_confirm')
        data = {
            'uid': uid,
            'token': 'invalid-token-123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }

        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])

    def test_password_reset_confirm_invalid_uid(self):
        """Test password reset with invalid user ID"""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)

        url = reverse('accounts_api:password_reset_confirm')
        data = {
            'uid': 'invalid-uid',
            'token': token,
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }

        response = self.client.post(
            url,
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()['success'])


class PasswordResetWebViewTestCase(TestCase):
    """Test password reset web views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123',
            role=User.Role.BUYER,
            is_active=True
        )

    def test_password_reset_request_view_get(self):
        """Test GET request to password reset request page"""
        url = reverse('accounts:password_reset_request')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_reset_request.html')

    def test_password_reset_request_view_post(self):
        """Test POST request to password reset request page"""
        url = reverse('accounts:password_reset_request')
        data = {'email': 'test@example.com'}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_confirm_view_valid_token(self):
        """Test password reset confirm view with valid token"""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        url = reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': token
        })

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_reset_confirm.html')
        self.assertTrue(response.context['validlink'])

    def test_password_reset_confirm_view_invalid_token(self):
        """Test password reset confirm view with invalid token"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        url = reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': 'invalid-token'
        })

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_reset_confirm.html')
        self.assertFalse(response.context['validlink'])

    def test_password_reset_confirm_view_post_success(self):
        """Test password reset confirm POST with valid data"""
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        url = reverse('accounts:password_reset_confirm', kwargs={
            'uidb64': uid,
            'token': token
        })

        data = {
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
