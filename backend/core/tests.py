from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Contact, Task

User = get_user_model()


class UserModelTest(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='Password123!',
            first_name='Test',
            last_name='User',
            color='#1FD7C1'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertTrue(user.check_password('Password123!'))
        self.assertEqual(user.color, '#1FD7C1')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='AdminPassword123!'
        )
        self.assertEqual(admin_user.username, 'adminuser')
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class RegistrationApiTest(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')

    def test_registration_success(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "repeated_password": "StrongPassword123!",
            "first_name": "New",
            "last_name": "User",
            "color": "#0099FF"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_password_mismatch(self):
        data = {
            "username": "mismatchuser",
            "email": "mismatch@example.com",
            "password": "StrongPassword123!",
            "repeated_password": "DifferentPassword123!"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_registration_duplicate_username(self):
        User.objects.create_user(username='existinguser', email='existing@example.com', password='Password123!')
        data = {
            "username": "existinguser",
            "email": "another@example.com",
            "password": "StrongPassword123!",
            "repeated_password": "StrongPassword123!"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)


class LoginApiTest(APITestCase):

    def setUp(self):
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='activeuser',
            email='active@example.com',
            password='SecretPassword123!',
            first_name='Active',
            last_name='User',
            color='#FF5500'
        )

    def test_login_success_with_username(self):
        data = {
            "username": "activeuser",
            "password": "SecretPassword123!"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'activeuser')
        self.assertEqual(response.data['color'], '#FF5500')

    def test_login_success_with_email(self):
        data = {
            "email": "active@example.com",
            "password": "SecretPassword123!"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['email'], 'active@example.com')

    def test_login_invalid_password(self):
        data = {
            "username": "activeuser",
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        data = {
            "username": "unknownuser",
            "password": "SomePassword123!"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutApiTest(APITestCase):

    def setUp(self):
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(
            username='logoutuser',
            email='logout@example.com',
            password='Password123!'
        )
        self.token = Token.objects.create(user=self.user)

    def test_logout_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_logout_unauthenticated(self):
        response = self.client.post(self.logout_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class UserProfileApiTest(APITestCase):

    def setUp(self):
        self.profile_url = reverse('user-profile')
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='Password123!',
            first_name='Profile',
            last_name='User',
            color='#1FD7C1'
        )
        self.token = Token.objects.create(user=self.user)

    def test_get_profile_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'profileuser')
        self.assertEqual(response.data['email'], 'profile@example.com')
        self.assertEqual(response.data['color'], '#1FD7C1')

    def test_get_profile_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_get_profile_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalidtoken12345')
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class ContactApiTest(APITestCase):

    def setUp(self):
        self.contacts_url = reverse('contact-list-create')
        self.user = User.objects.create_user(
            username='contacttestuser',
            email='contacttestuser@example.com',
            password='Password123!'
        )
        self.token = Token.objects.create(user=self.user)
        self.contact = Contact.objects.create(
            name='Jane Doe',
            email='jane@example.com',
            phone='+491512345678',
            color='#FF7A00'
        )
        self.contact_detail_url = reverse('contact-detail', kwargs={'pk': self.contact.pk})

    def test_get_contacts_list(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(self.contacts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_contact_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {
            "name": "Max Mustermann",
            "email": "max@example.com",
            "phone": "+491709876543",
            "color": "#1FD7C1"
        }
        response = self.client.post(self.contacts_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Max Mustermann')
        self.assertTrue(Contact.objects.filter(email='max@example.com').exists())

    def test_get_contact_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(self.contact_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Jane Doe')

    def test_update_contact(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+491512345678",
            "color": "#9327FF"
        }
        response = self.client.put(self.contact_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.name, 'Jane Smith')

    def test_delete_contact(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.delete(self.contact_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Contact.objects.filter(pk=self.contact.pk).exists())


class TaskApiTest(APITestCase):

    def setUp(self):
        self.tasks_url = reverse('task-list-create')
        self.user = User.objects.create_user(
            username='taskuser',
            email='taskuser@example.com',
            password='Password123!'
        )
        self.token = Token.objects.create(user=self.user)
        self.contact = Contact.objects.create(
            name='Assignee Contact',
            email='assignee@example.com',
            color='#FF7A00'
        )

    def test_create_task_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {
            "title": "Implement REST API",
            "description": "Build Task creation endpoint for KanMind.",
            "due_date": "2026-12-31",
            "priority": "urgent",
            "status": "in_progress",
            "category": "Technical Task",
            "assigned_to": [self.contact.id]
        }
        response = self.client.post(self.tasks_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Implement REST API')
        self.assertEqual(response.data['priority'], 'urgent')
        self.assertEqual(len(response.data['assigned_to_details']), 1)
        self.assertEqual(response.data['assigned_to_details'][0]['name'], 'Assignee Contact')
        self.assertTrue(Task.objects.filter(title='Implement REST API').exists())

    def test_create_task_unauthenticated(self):
        data = {
            "title": "Unauthorized Task"
        }
        response = self.client.post(self.tasks_url, data)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_tasks(self):
        Task.objects.create(title="Existing Task 1", status="to_do")
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(self.tasks_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
