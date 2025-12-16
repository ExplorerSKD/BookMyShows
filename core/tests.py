from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import UserProfile


class LoginPortalTests(TestCase):
    def setUp(self):
        self.organizer = self._create_user(
            username='organizer_user',
            password='pass12345',
            role=UserProfile.ROLE_ORGANIZER,
        )
        self.staff = self._create_user(
            username='staff_user',
            password='pass67890',
            role=UserProfile.ROLE_STAFF,
        )
        self.customer = self._create_user(
            username='customer_user',
            password='custpass',
            role=UserProfile.ROLE_CUSTOMER,
        )

    def _create_user(self, username, password, role):
        user = User.objects.create_user(username=username, password=password)
        profile = user.profile  # auto-created via signal
        profile.role = role
        profile.is_role_approved = True
        profile.save(update_fields=['role', 'is_role_approved'])
        return user

    def test_organizer_portal_accepts_valid_credentials(self):
        response = self.client.post(
            reverse('organizer_login'),
            {'username': 'organizer_user', 'password': 'pass12345'}
        )
        self.assertRedirects(response, reverse('organizer_dashboard'))

    def test_organizer_portal_rejects_non_organizer_role(self):
        response = self.client.post(
            reverse('organizer_login'),
            {'username': 'staff_user', 'password': 'pass67890'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'restricted', status_code=200)

    def test_staff_portal_accepts_valid_credentials(self):
        response = self.client.post(
            reverse('staff_login'),
            {'username': 'staff_user', 'password': 'pass67890'}
        )
        self.assertRedirects(response, reverse('staff_scan_ticket'))

    def test_staff_portal_rejects_non_staff_role(self):
        response = self.client.post(
            reverse('staff_login'),
            {'username': 'organizer_user', 'password': 'pass12345'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'restricted', status_code=200)

    def test_portal_rejects_pending_approval(self):
        pending_user = self._create_user(
            username='pending_org',
            password='pending123',
            role=UserProfile.ROLE_ORGANIZER,
        )
        pending_profile = pending_user.profile
        pending_profile.is_role_approved = False
        pending_profile.save(update_fields=['is_role_approved'])

        response = self.client.post(
            reverse('organizer_login'),
            {'username': 'pending_org', 'password': 'pending123'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'pending admin approval')


class RegistrationRoleTests(TestCase):
    def test_customer_registration_auto_approved(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'new_customer',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
                'role': UserProfile.ROLE_CUSTOMER,
            }
        )
        self.assertRedirects(response, reverse('home'))
        profile = User.objects.get(username='new_customer').profile
        self.assertTrue(profile.is_role_approved)
        self.assertEqual(profile.role, UserProfile.ROLE_CUSTOMER)
        self.assertEqual(int(self.client.session['_auth_user_id']), profile.user.id)

    def test_organizer_registration_marks_pending(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'new_org',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
                'role': UserProfile.ROLE_ORGANIZER,
            }
        )
        self.assertRedirects(response, reverse('login'))
        profile = User.objects.get(username='new_org').profile
        self.assertFalse(profile.is_role_approved)
        self.assertEqual(profile.role, UserProfile.ROLE_ORGANIZER)
        self.assertIsNone(self.client.session.get('_auth_user_id'))
