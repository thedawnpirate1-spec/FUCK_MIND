from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Contact, Task, Subtask, Board, Comment

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
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='Password123!'
        )
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
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )


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
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_get_profile_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token invalidtoken12345')
        response = self.client.get(self.profile_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )


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
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_list_tasks(self):
        Task.objects.create(title="Existing Task 1", status="to_do")
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(self.tasks_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_filter_tasks_by_status(self):
        Task.objects.create(title="Task A", status="to_do")
        Task.objects.create(title="Task B", status="in_progress")
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{self.tasks_url}?status=in_progress")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(task['status'] == 'in_progress' for task in response.data))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Task B')

    def test_filter_tasks_by_priority(self):
        Task.objects.create(title="Low Task", priority="low")
        Task.objects.create(title="Urgent Task", priority="urgent")
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{self.tasks_url}?priority=urgent")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(task['priority'] == 'urgent' for task in response.data))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Urgent Task')

    def test_filter_tasks_by_search(self):
        Task.objects.create(title="Backend Refactoring", description="Refactor DRF views.")
        Task.objects.create(title="Frontend Design", description="Update CSS styling.")
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{self.tasks_url}?search=refactor")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Backend Refactoring')

    def test_filter_tasks_by_assigned_to(self):
        t1 = Task.objects.create(title="Assigned Task")
        t1.assigned_to.add(self.contact)
        Task.objects.create(title="Unassigned Task")
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{self.tasks_url}?assigned_to={self.contact.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Assigned Task')

    def test_get_task_detail(self):
        task = Task.objects.create(title="Detail Task", status="to_do")
        detail_url = reverse('task-detail', kwargs={'pk': task.pk})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Detail Task')

    def test_patch_task_status_drag_and_drop(self):
        task = Task.objects.create(title="Drag Drop Task", status="to_do")
        detail_url = reverse('task-detail', kwargs={'pk': task.pk})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {"status": "in_progress"}
        response = self.client.patch(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, 'in_progress')

    def test_put_task_full_update(self):
        task = Task.objects.create(title="Old Title", priority="low", status="to_do")
        detail_url = reverse('task-detail', kwargs={'pk': task.pk})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {
            "title": "New Updated Title",
            "description": "Updated Description",
            "priority": "urgent",
            "status": "done",
            "category": "User Story"
        }
        response = self.client.put(detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.title, 'New Updated Title')
        self.assertEqual(task.status, 'done')
        self.assertEqual(task.priority, 'urgent')

    def test_delete_task_success_with_cascade(self):
        task = Task.objects.create(title="Task to delete", created_by=self.user)
        task.assigned_to.add(self.contact)
        subtask1 = Subtask.objects.create(task=task, title="Subtask 1")
        subtask2 = Subtask.objects.create(task=task, title="Subtask 2")
        detail_url = reverse('task-detail', kwargs={'pk': task.pk})

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        # Cascade checks: subtasks must be removed
        self.assertFalse(Subtask.objects.filter(pk=subtask1.pk).exists())
        self.assertFalse(Subtask.objects.filter(pk=subtask2.pk).exists())
        # Integrity checks: assigned contacts and user must NOT be deleted
        self.assertTrue(Contact.objects.filter(pk=self.contact.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_delete_task_unauthenticated(self):
        task = Task.objects.create(title="Unauthorized delete task")
        detail_url = reverse('task-detail', kwargs={'pk': task.pk})
        response = self.client.delete(detail_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())

    def test_delete_task_not_found(self):
        detail_url = reverse('task-detail', kwargs={'pk': 99999})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SubtaskApiTest(APITestCase):

    def setUp(self):
        self.subtasks_url = reverse('subtask-list-create')
        self.user = User.objects.create_user(
            username='subtaskuser',
            email='subtaskuser@example.com',
            password='Password123!'
        )
        self.token = Token.objects.create(user=self.user)
        self.task = Task.objects.create(
            title='Parent Task',
            created_by=self.user
        )

    def test_create_subtask(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {
            "task": self.task.id,
            "title": "Subtask 1",
            "is_completed": False
        }
        response = self.client.post(self.subtasks_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Subtask 1')
        self.assertEqual(response.data['task'], self.task.id)

    def test_list_subtasks_filtered_by_task(self):
        Subtask.objects.create(task=self.task, title="Sub 1")
        other_task = Task.objects.create(title="Other Task")
        Subtask.objects.create(task=other_task, title="Sub 2")

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(f"{self.subtasks_url}?task={self.task.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Sub 1')

    def test_toggle_subtask_is_completed(self):
        subtask = Subtask.objects.create(task=self.task, title="Checkbox Test", is_completed=False)
        detail_url = reverse('subtask-detail', kwargs={'pk': subtask.pk})

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.patch(detail_url, {"is_completed": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subtask.refresh_from_db()
        self.assertTrue(subtask.is_completed)

    def test_subtasks_included_in_task_detail(self):
        Subtask.objects.create(task=self.task, title="Nested Subtask")
        task_detail_url = reverse('task-detail', kwargs={'pk': self.task.pk})

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(task_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('subtasks', response.data)
        self.assertEqual(len(response.data['subtasks']), 1)
        self.assertEqual(response.data['subtasks'][0]['title'], 'Nested Subtask')

    def test_delete_subtask_success(self):
        subtask = Subtask.objects.create(task=self.task, title="Delete Me")
        detail_url = reverse('subtask-detail', kwargs={'pk': subtask.pk})

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subtask.objects.filter(pk=subtask.pk).exists())
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())


class ErrorHandlingApiTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='errortestuser',
            email='errortest@example.com',
            password='Password123!'
        )
        self.token = Token.objects.create(user=self.user)

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(reverse('task-list-create'))
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )
        self.assertIn('detail', response.data)

    def test_not_found_endpoint_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(reverse('task-detail', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

    def test_custom_exception_handler_handles_500(self):
        from .exceptions import custom_exception_handler
        exc = Exception("Unexpected internal error")
        response = custom_exception_handler(exc, {})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data.get('detail'), 'An internal server error occurred.')

    def test_custom_404_view_response(self):
        from .views import custom_404_view
        response = custom_404_view(None)
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'The requested resource was not found.', response.content)

    def test_custom_500_view_response(self):
        from .views import custom_500_view
        response = custom_500_view(None)
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'An internal server error occurred.', response.content)


class CorsApiTest(APITestCase):

    def test_cors_preflight_options_request(self):
        response = self.client.options(
            reverse('task-list-create'),
            HTTP_ORIGIN='http://localhost:3000',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_cors_headers_present_on_get(self):
        response = self.client.get(
            reverse('task-list-create'),
            HTTP_ORIGIN='http://localhost:3000'
        )
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'http://localhost:3000')


class AuthHeaderIntegrationTest(APITestCase):
    """
    Tests for flexible auth headers (Bearer, Token, case-insensitive, error handling).
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='authheadertestuser',
            email='authheadertest@example.com',
            password='Password123!'
        )
        self.token = Token.objects.create(user=self.user)
        self.url = reverse('user-profile')

    def test_bearer_token_authorization(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=f'Bearer {self.token.key}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'authheadertestuser')

    def test_lowercase_bearer_token_authorization(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=f'bearer {self.token.key}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_standard_token_authorization(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lowercase_token_authorization(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=f'token {self.token.key}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_malformed_auth_header_empty(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_malformed_auth_header_extra_parts(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer part1 part2')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_returns_401(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer non_existent_token_12345')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PayloadEdgeCasesTest(APITestCase):
    """
    Tests for payload edge cases (nested subtasks, empty fields, whitespace).
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='payloaduser',
            email='payloaduser@example.com',
            password='Password123!'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token.key)
        self.contact = Contact.objects.create(name='Test Contact', email='contact@example.com')

    def test_create_task_with_nested_subtasks_dict(self):
        data = {
            "title": "Task with Nested Subtasks",
            "due_date": "2026-11-01",
            "category": "User Story",
            "priority": "urgent",
            "status": "to_do",
            "subtasks": [
                {"title": "First Subtask"},
                {"title": "Second Subtask"}
            ]
        }
        response = self.client.post(reverse('task-list-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['subtasks']), 2)
        task_id = response.data['id']
        self.assertEqual(Subtask.objects.filter(task_id=task_id).count(), 2)

    def test_create_task_with_nested_subtasks_string_list(self):
        data = {
            "title": "Task with String Subtasks",
            "due_date": "2026-11-02",
            "subtasks": ["Quick Subtask 1", "Quick Subtask 2"]
        }
        response = self.client.post(reverse('task-list-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['subtasks']), 2)
        self.assertEqual(response.data['subtasks'][0]['title'], 'Quick Subtask 1')

    def test_create_task_with_empty_due_date_string(self):
        data = {
            "title": "Task without Due Date",
            "due_date": ""
        }
        response = self.client.post(reverse('task-list-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['due_date'])

    def test_create_task_with_assigned_to_null(self):
        data = {
            "title": "Task with Null Assigned",
            "assigned_to": None
        }
        response = self.client.post(reverse('task-list-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['assigned_to'], [])

    def test_create_task_normalizes_uppercase_status_and_priority(self):
        data = {
            "title": "Case Insensitive Task",
            "status": "IN_PROGRESS",
            "priority": "URGENT"
        }
        response = self.client.post(reverse('task-list-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['priority'], 'urgent')

    def test_contact_trims_whitespace_and_lowercases_email(self):
        data = {
            "name": "   Jane Doe   ",
            "email": "  JANE.DOE@EXAMPLE.COM  ",
            "phone": "0123456789"
        }
        response = self.client.post(reverse('contact-list-create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Jane Doe')
        self.assertEqual(response.data['email'], 'jane.doe@example.com')

    def test_login_trims_whitespace(self):
        data = {
            "username": "   payloaduser   ",
            "password": "Password123!"
        }
        response = self.client.post(reverse('login'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class SwaggerApiDocumentationTest(APITestCase):
    """
    Tests for OpenAPI schema and Swagger UI endpoints.
    """

    def test_schema_endpoint_returns_200(self):
        response = self.client.get(reverse('schema'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_ui_endpoint_returns_200(self):
        response = self.client.get(reverse('swagger-ui'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_redoc_endpoint_returns_200(self):
        response = self.client.get(reverse('redoc'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FrontendIntegrationTest(APITestCase):
    """
    Tests for frontend endpoints (registration/login with full name,
    email check, boards, comments, dashboard).
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='maxmustermann',
            email='max@example.com',
            password='Password123!',
            first_name='Max',
            last_name='Mustermann'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_registration_with_fullname_no_username(self):
        data = {
            "fullname": "Erika Mustermann",
            "email": "erika.mustermann@example.com",
            "password": "SafePassword123!",
            "repeated_password": "SafePassword123!"
        }
        response = self.client.post(reverse('registration-frontend'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['fullname'], 'Erika Mustermann')

    def test_login_returns_fullname(self):
        data = {
            "email": "max@example.com",
            "password": "Password123!"
        }
        response = self.client.post(reverse('login-frontend'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['fullname'], 'Max Mustermann')

    def test_email_check_existing_user(self):
        response = self.client.get(reverse('email-check') + '?email=max@example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'max@example.com')
        self.assertEqual(response.data['fullname'], 'Max Mustermann')

    def test_email_check_non_existing_user(self):
        response = self.client.get(reverse('email-check') + '?email=unknown@example.com')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_board_crud_flow(self):
        other_user = User.objects.create_user(
            username='colleague',
            email='colleague@example.com',
            password='Password123!',
            first_name='Colleague',
            last_name='User'
        )
        create_data = {
            "title": "Marketing Sprint",
            "members": [self.user.id, other_user.id]
        }
        create_resp = self.client.post(reverse('board-list-create'), create_data, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        board_id = create_resp.data['id']
        self.assertEqual(len(create_resp.data['members']), 2)

        detail_resp = self.client.get(reverse('board-detail', kwargs={'pk': board_id}))
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data['title'], 'Marketing Sprint')

    def test_task_with_board_assignee_reviewer_and_comments(self):
        board = Board.objects.create(title="Dev Board", owner=self.user)
        board.members.add(self.user)

        task_data = {
            "board": board.id,
            "title": "Implement Frontend Hook",
            "description": "Connect API",
            "status": "to_do",
            "priority": "urgent",
            "assignee_id": self.user.id,
            "reviewer_id": self.user.id,
            "due_date": "2026-11-15"
        }
        task_resp = self.client.post(reverse('task-list-create'), task_data, format='json')
        self.assertEqual(task_resp.status_code, status.HTTP_201_CREATED)
        task_id = task_resp.data['id']
        self.assertEqual(task_resp.data['board'], board.id)
        self.assertEqual(task_resp.data['assignee']['id'], self.user.id)

        assigned_resp = self.client.get(reverse('tasks-assigned-to-me'))
        self.assertEqual(assigned_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(assigned_resp.data), 1)

        reviewing_resp = self.client.get(reverse('tasks-reviewing'))
        self.assertEqual(reviewing_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(reviewing_resp.data), 1)

        comment_resp = self.client.post(
            reverse('task-comments', kwargs={'task_id': task_id}),
            {"content": "Looks good so far!"},
            format='json'
        )
        self.assertEqual(comment_resp.status_code, status.HTTP_201_CREATED)
        comment_id = comment_resp.data['id']
        self.assertEqual(comment_resp.data['author'], 'Max Mustermann')

        list_comments = self.client.get(reverse('task-comments', kwargs={'task_id': task_id}))
        self.assertEqual(list_comments.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_comments.data), 1)

        del_comment = self.client.delete(
            reverse('task-comment-detail', kwargs={'task_id': task_id, 'pk': comment_id})
        )
        self.assertEqual(del_comment.status_code, status.HTTP_204_NO_CONTENT)

    def test_board_metrics_and_task_frontend_representation(self):
        colleague = User.objects.create_user(
            username='colleague2',
            email='colleague2@example.com',
            password='Password123!'
        )
        board = Board.objects.create(title="Metrics Board", owner=self.user)
        board.members.add(self.user, colleague)

        Task.objects.create(
            board=board,
            title="Urgent ToDo Task",
            status="to_do",
            priority="urgent",
            assignee=self.user,
            created_by=self.user
        )

        board_resp = self.client.get(reverse('board-detail', kwargs={'pk': board.id}))
        self.assertEqual(board_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(board_resp.data['owner']['id'], self.user.id)
        self.assertEqual(board_resp.data['owner']['email'], self.user.email)
        self.assertEqual(board_resp.data['owner']['full_name'], 'Max Mustermann')
        self.assertEqual(len(board_resp.data['members']), 2)
        self.assertIn('full_name', board_resp.data['members'][0])

        assigned_resp = self.client.get(reverse('tasks-assigned-to-me'))
        self.assertEqual(assigned_resp.status_code, status.HTTP_200_OK)
        assigned_urgent = next(t for t in assigned_resp.data if t['title'] == 'Urgent ToDo Task')
        self.assertEqual(assigned_urgent['status'], 'to-do')
        self.assertEqual(assigned_urgent['priority'], 'high')

    def test_board_and_task_permissions_and_status_codes(self):
        outsider = User.objects.create_user(
            username='outsider',
            email='outsider@example.com',
            password='Password123!'
        )
        outsider_token = Token.objects.create(user=outsider)

        board = Board.objects.create(title="Private Board", owner=self.user)
        board.members.add(self.user)
        task = Task.objects.create(board=board, title="Private Task", created_by=self.user)
        comment = Comment.objects.create(task=task, author=self.user, content="Owner comment")

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {outsider_token.key}')

        get_resp = self.client.get(reverse('board-detail', kwargs={'pk': board.id}))
        self.assertEqual(get_resp.status_code, status.HTTP_403_FORBIDDEN)

        patch_resp = self.client.patch(
            reverse('board-detail', kwargs={'pk': board.id}),
            {'title': 'Hacked'}
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_403_FORBIDDEN)

        del_resp = self.client.delete(reverse('board-detail', kwargs={'pk': board.id}))
        self.assertEqual(del_resp.status_code, status.HTTP_403_FORBIDDEN)

        create_404 = self.client.post(reverse('task-list-create'), {
            'board': 9999,
            'title': 'No Board Task'
        })
        self.assertEqual(create_404.status_code, status.HTTP_404_NOT_FOUND)

        create_404_board_id = self.client.post(reverse('task-list-create'), {
            'board_id': 4000,
            'title': 'No Board Task via board_id'
        })
        self.assertEqual(create_404_board_id.status_code, status.HTTP_404_NOT_FOUND)

        create_403 = self.client.post(reverse('task-list-create'), {
            'board': board.id,
            'title': 'Forbidden Task'
        })
        self.assertEqual(create_403.status_code, status.HTTP_403_FORBIDDEN)

        create_403_board_id = self.client.post(reverse('task-list-create'), {
            'board_id': board.id,
            'title': 'Forbidden Task via board_id'
        })
        self.assertEqual(create_403_board_id.status_code, status.HTTP_403_FORBIDDEN)

        comment_404 = self.client.get(
            reverse('task-comments', kwargs={'task_id': 9999})
        )
        self.assertEqual(comment_404.status_code, status.HTTP_404_NOT_FOUND)

        comment_403 = self.client.get(
            reverse('task-comments', kwargs={'task_id': task.id})
        )
        self.assertEqual(comment_403.status_code, status.HTTP_403_FORBIDDEN)

        del_task_403 = self.client.delete(reverse('task-detail', kwargs={'pk': task.id}))
        self.assertEqual(del_task_403.status_code, status.HTTP_403_FORBIDDEN)

        del_comment_403 = self.client.delete(
            reverse('task-comment-detail', kwargs={'task_id': task.id, 'pk': comment.id})
        )
        self.assertEqual(del_comment_403.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_patch_response_schema(self):
        board = Board.objects.create(title="Sprint Board", owner=self.user)
        board.members.add(self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        patch_resp = self.client.patch(
            reverse('board-detail', kwargs={'pk': board.id}),
            {'title': 'Renamed Sprint Board'},
            format='json'
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertIn('members', patch_resp.data)
        self.assertIn('owner', patch_resp.data)
        self.assertEqual(set(patch_resp.data.keys()), {'id', 'title', 'members', 'owner'})

        member_entry = patch_resp.data['members'][0]
        self.assertEqual(set(member_entry.keys()), {'id', 'email', 'full_name'})
        self.assertEqual(member_entry['id'], self.user.id)
        self.assertEqual(member_entry['email'], self.user.email)
        self.assertEqual(member_entry['full_name'], 'Max Mustermann')

        owner_entry = patch_resp.data['owner']
        self.assertEqual(set(owner_entry.keys()), {'id', 'email', 'full_name'})
        self.assertEqual(owner_entry['id'], self.user.id)
        self.assertEqual(owner_entry['email'], self.user.email)
        self.assertEqual(owner_entry['full_name'], 'Max Mustermann')








