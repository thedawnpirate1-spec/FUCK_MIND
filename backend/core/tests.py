from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from .models import Board, Comment, Task

User = get_user_model()

PASSWORD = 'Password123!'

AUTH_KEYS = {'token', 'fullname', 'email', 'user_id'}
USER_KEYS = {'id', 'email', 'fullname'}
BOARD_SUMMARY_KEYS = {
    'id', 'title', 'member_count', 'ticket_count',
    'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id'
}
BOARD_DETAIL_KEYS = {'id', 'title', 'owner_id', 'members', 'tasks'}
BOARD_UPDATE_KEYS = {'id', 'title', 'owner_data', 'members_data'}
BOARD_TASK_KEYS = {
    'id', 'title', 'description', 'status', 'priority',
    'assignee', 'reviewer', 'due_date', 'comments_count'
}
TASK_KEYS = BOARD_TASK_KEYS | {'board'}
TASK_UPDATE_KEYS = {
    'id', 'title', 'description', 'status', 'priority',
    'assignee', 'reviewer', 'due_date'
}
COMMENT_KEYS = {'id', 'created_at', 'author', 'content'}


class ApiTestBase(APITestCase):
    """
    Shared helpers: user creation, token authentication and a prepared board.
    """

    def make_user(self, name, first_name='', last_name=''):
        return User.objects.create_user(
            username=name,
            email=f'{name}@example.com',
            password=PASSWORD,
            first_name=first_name,
            last_name=last_name
        )

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def make_board(self, owner, members=()):
        board = Board.objects.create(title='Test Board', owner=owner)
        board.members.add(*members)
        return board

    def make_task(self, board, creator, **kwargs):
        return Task.objects.create(
            board=board, title=kwargs.pop('title', 'Test Task'),
            created_by=creator, **kwargs
        )


class UserModelTest(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password=PASSWORD,
            first_name='Test',
            last_name='User'
        )
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.fullname, 'Test User')
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username='adminuser', email='admin@example.com', password=PASSWORD
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class RegistrationApiTest(ApiTestBase):

    def setUp(self):
        self.url = reverse('registration')
        self.data = {
            'fullname': 'Example Username',
            'email': 'example@mail.de',
            'password': 'examplePassword1!',
            'repeated_password': 'examplePassword1!'
        }

    def test_registration_success(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), AUTH_KEYS)
        self.assertEqual(response.data['fullname'], 'Example Username')
        self.assertEqual(response.data['email'], 'example@mail.de')
        user = User.objects.get(email='example@mail.de')
        self.assertEqual(response.data['user_id'], user.id)
        self.assertEqual(response.data['token'], Token.objects.get(user=user).key)

    def test_registration_password_mismatch(self):
        self.data['repeated_password'] = 'somethingElse1!'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        self.make_user('existing')
        self.data['email'] = 'existing@example.com'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_missing_fullname(self):
        del self.data['fullname']
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fullname', response.data)

    def test_registration_creates_unique_usernames(self):
        self.client.post(self.url, self.data, format='json')
        self.data['email'] = 'example@other.de'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)


class LoginApiTest(ApiTestBase):

    def setUp(self):
        self.url = reverse('login')
        self.user = self.make_user('active', 'Active', 'User')

    def test_login_success(self):
        response = self.client.post(
            self.url, {'email': 'active@example.com', 'password': PASSWORD}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), AUTH_KEYS)
        self.assertEqual(response.data['fullname'], 'Active User')
        self.assertEqual(response.data['user_id'], self.user.id)

    def test_login_email_is_case_insensitive(self):
        response = self.client.post(
            self.url, {'email': 'ACTIVE@example.com', 'password': PASSWORD}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_invalid_password(self):
        response = self.client.post(
            self.url, {'email': 'active@example.com', 'password': 'wrong'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unknown_email(self):
        response = self.client.post(
            self.url, {'email': 'nobody@example.com', 'password': PASSWORD}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_fields(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailCheckApiTest(ApiTestBase):

    def setUp(self):
        self.url = reverse('email-check')
        self.user = self.make_user('max', 'Max', 'Mustermann')
        self.authenticate(self.user)

    def test_existing_email(self):
        response = self.client.get(self.url, {'email': 'max@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), USER_KEYS)
        self.assertEqual(response.data['id'], self.user.id)
        self.assertEqual(response.data['fullname'], 'Max Mustermann')

    def test_unknown_email_returns_404(self):
        response = self.client.get(self.url, {'email': 'unknown@example.com'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_email_returns_400(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_400_BAD_REQUEST)

    def test_malformed_email_returns_400(self):
        response = self.client.get(self.url, {'email': 'not-an-email'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        response = self.client.get(self.url, {'email': 'max@example.com'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BoardCreateListApiTest(ApiTestBase):

    def setUp(self):
        self.url = reverse('board-list-create')
        self.owner = self.make_user('owner', 'Olivia', 'Owner')
        self.member = self.make_user('member', 'Mike', 'Member')
        self.outsider = self.make_user('outsider')
        self.authenticate(self.owner)

    def test_create_board_response_shape(self):
        data = {'title': 'New Project', 'members': [self.owner.id, self.member.id]}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), BOARD_SUMMARY_KEYS)
        self.assertEqual(response.data['title'], 'New Project')
        self.assertEqual(response.data['member_count'], 2)
        self.assertEqual(response.data['ticket_count'], 0)
        self.assertEqual(response.data['tasks_to_do_count'], 0)
        self.assertEqual(response.data['tasks_high_prio_count'], 0)
        self.assertEqual(response.data['owner_id'], self.owner.id)

    def test_create_board_owner_is_requesting_user(self):
        response = self.client.post(
            self.url, {'title': 'Mine', 'members': [self.member.id]}, format='json'
        )
        board = Board.objects.get(pk=response.data['id'])
        self.assertEqual(board.owner, self.owner)
        self.assertEqual(response.data['member_count'], 1)

    def test_create_board_invalid_member_returns_400(self):
        response = self.client.post(
            self.url, {'title': 'Broken', 'members': [99999]}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_board_without_title_returns_400(self):
        response = self.client.post(self.url, {'members': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_board_unauthenticated_returns_401(self):
        self.client.credentials()
        response = self.client.post(self.url, {'title': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_boards_response_shape_and_counters(self):
        board = self.make_board(self.owner, [self.owner, self.member])
        self.make_task(board, self.owner, status='to-do', priority='high')
        self.make_task(board, self.owner, status='to-do', priority='low')
        self.make_task(board, self.owner, status='done', priority='high')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        entry = response.data[0]
        self.assertEqual(set(entry.keys()), BOARD_SUMMARY_KEYS)
        self.assertEqual(entry['member_count'], 2)
        self.assertEqual(entry['ticket_count'], 3)
        self.assertEqual(entry['tasks_to_do_count'], 2)
        self.assertEqual(entry['tasks_high_prio_count'], 2)
        self.assertEqual(entry['owner_id'], self.owner.id)

    def test_list_contains_only_own_and_member_boards(self):
        own = self.make_board(self.owner)
        joined = self.make_board(self.member, [self.owner])
        self.make_board(self.member)
        response = self.client.get(self.url)
        ids = {entry['id'] for entry in response.data}
        self.assertEqual(ids, {own.id, joined.id})

    def test_list_unauthenticated_returns_401(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)


class BoardDetailApiTest(ApiTestBase):

    def setUp(self):
        self.owner = self.make_user('owner', 'Olivia', 'Owner')
        self.member = self.make_user('member', 'Mike', 'Member')
        self.outsider = self.make_user('outsider')
        self.board = self.make_board(self.owner, [self.owner, self.member])
        self.url = reverse('board-detail', kwargs={'board_id': self.board.id})

    def test_get_board_detail_shape(self):
        task = self.make_task(
            self.board, self.owner, assignee=self.member, reviewer=self.owner
        )
        Comment.objects.create(task=task, author=self.member, content='Hi')
        self.authenticate(self.member)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), BOARD_DETAIL_KEYS)
        self.assertEqual(response.data['owner_id'], self.owner.id)
        self.assertEqual(len(response.data['members']), 2)
        for member in response.data['members']:
            self.assertEqual(set(member.keys()), USER_KEYS)

        self.assertEqual(len(response.data['tasks']), 1)
        task_data = response.data['tasks'][0]
        self.assertEqual(set(task_data.keys()), BOARD_TASK_KEYS)
        self.assertEqual(set(task_data['assignee'].keys()), USER_KEYS)
        self.assertEqual(task_data['reviewer']['id'], self.owner.id)
        self.assertEqual(task_data['comments_count'], 1)

    def test_get_board_detail_owner_allowed(self):
        self.authenticate(self.owner)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

    def test_get_board_detail_outsider_returns_403(self):
        self.authenticate(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_get_board_detail_not_found(self):
        self.authenticate(self.owner)
        url = reverse('board-detail', kwargs={'board_id': 99999})
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_get_board_detail_unauthenticated_returns_401(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_board_response_shape(self):
        third = self.make_user('third', 'Tina', 'Third')
        self.authenticate(self.owner)
        response = self.client.patch(
            self.url, {'title': 'Changed title', 'members': [self.owner.id, third.id]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), BOARD_UPDATE_KEYS)
        self.assertEqual(response.data['title'], 'Changed title')
        self.assertEqual(set(response.data['owner_data'].keys()), USER_KEYS)
        self.assertEqual(response.data['owner_data']['fullname'], 'Olivia Owner')
        members = response.data['members_data']
        self.assertEqual({m['id'] for m in members}, {self.owner.id, third.id})
        for member in members:
            self.assertEqual(set(member.keys()), USER_KEYS)

    def test_patch_board_removes_unlisted_members(self):
        self.authenticate(self.owner)
        self.client.patch(self.url, {'members': [self.owner.id]}, format='json')
        self.assertEqual(list(self.board.members.all()), [self.owner])

    def test_patch_board_allowed_for_member(self):
        self.authenticate(self.member)
        response = self.client.patch(self.url, {'title': 'By member'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_board_invalid_member_returns_400(self):
        self.authenticate(self.owner)
        response = self.client.patch(self.url, {'members': [99999]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_board_outsider_returns_403(self):
        self.authenticate(self.outsider)
        response = self.client.patch(self.url, {'title': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_board_not_found(self):
        self.authenticate(self.owner)
        url = reverse('board-detail', kwargs={'board_id': 99999})
        self.assertEqual(
            self.client.patch(url, {'title': 'x'}, format='json').status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_put_is_not_allowed(self):
        self.authenticate(self.owner)
        response = self.client.put(self.url, {'title': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_board_as_owner(self):
        task = self.make_task(self.board, self.owner)
        self.authenticate(self.owner)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Board.objects.filter(pk=self.board.pk).exists())
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_delete_board_as_member_returns_403(self):
        self.authenticate(self.member)
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Board.objects.filter(pk=self.board.pk).exists())

    def test_delete_board_not_found(self):
        self.authenticate(self.owner)
        url = reverse('board-detail', kwargs={'board_id': 99999})
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_board_unauthenticated_returns_401(self):
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_401_UNAUTHORIZED)


class TaskCreateApiTest(ApiTestBase):

    def setUp(self):
        self.url = reverse('task-create')
        self.owner = self.make_user('owner', 'Olivia', 'Owner')
        self.member = self.make_user('member', 'Mike', 'Member')
        self.outsider = self.make_user('outsider')
        self.board = self.make_board(self.owner, [self.member])
        self.data = {
            'board': self.board.id,
            'title': 'Code-Review durchführen',
            'description': 'Den neuen PR prüfen',
            'status': 'review',
            'priority': 'medium',
            'assignee_id': self.member.id,
            'reviewer_id': self.owner.id,
            'due_date': '2025-02-27'
        }
        self.authenticate(self.member)

    def test_create_task_response_shape(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), TASK_KEYS)
        self.assertEqual(response.data['board'], self.board.id)
        self.assertEqual(response.data['status'], 'review')
        self.assertEqual(response.data['priority'], 'medium')
        self.assertEqual(response.data['due_date'], '2025-02-27')
        self.assertEqual(response.data['comments_count'], 0)
        self.assertEqual(set(response.data['assignee'].keys()), USER_KEYS)
        self.assertEqual(response.data['assignee']['id'], self.member.id)
        self.assertEqual(response.data['reviewer']['id'], self.owner.id)
        self.assertEqual(Task.objects.get(pk=response.data['id']).created_by, self.member)

    def test_create_task_without_assignee_and_reviewer(self):
        del self.data['assignee_id'], self.data['reviewer_id']
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['assignee'])
        self.assertIsNone(response.data['reviewer'])

    def test_create_task_as_board_owner(self):
        self.authenticate(self.owner)
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_task_invalid_status_returns_400(self):
        self.data['status'] = 'in_progress'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_invalid_priority_returns_400(self):
        self.data['priority'] = 'urgent'
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_without_board_returns_400(self):
        del self.data['board']
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_without_title_returns_400(self):
        del self.data['title']
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_assignee_not_board_member_returns_400(self):
        self.data['assignee_id'] = self.outsider.id
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('assignee_id', response.data)

    def test_create_task_reviewer_not_board_member_returns_400(self):
        self.data['reviewer_id'] = self.outsider.id
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reviewer_id', response.data)

    def test_create_task_board_not_found_returns_404(self):
        self.data['board'] = 99999
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_task_non_member_returns_403(self):
        self.authenticate(self.outsider)
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Task.objects.exists())

    def test_create_task_unauthenticated_returns_401(self):
        self.client.credentials()
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_tasks_is_not_part_of_the_api(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TaskUpdateDeleteApiTest(ApiTestBase):

    def setUp(self):
        self.owner = self.make_user('owner', 'Olivia', 'Owner')
        self.creator = self.make_user('creator', 'Chris', 'Creator')
        self.member = self.make_user('member', 'Mike', 'Member')
        self.outsider = self.make_user('outsider')
        self.board = self.make_board(self.owner, [self.creator, self.member])
        self.task = self.make_task(self.board, self.creator, status='to-do', priority='low')
        self.url = reverse('task-detail', kwargs={'task_id': self.task.id})

    def test_patch_task_response_shape(self):
        self.authenticate(self.member)
        data = {
            'title': 'Code-Review abschließen',
            'description': 'Feedback geben',
            'status': 'done',
            'priority': 'high',
            'assignee_id': self.member.id,
            'reviewer_id': self.owner.id,
            'due_date': '2025-02-28'
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), TASK_UPDATE_KEYS)
        self.assertEqual(response.data['status'], 'done')
        self.assertEqual(response.data['priority'], 'high')
        self.assertEqual(response.data['assignee']['id'], self.member.id)
        self.assertEqual(set(response.data['reviewer'].keys()), USER_KEYS)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Code-Review abschließen')

    def test_patch_task_partial_update_keeps_other_fields(self):
        self.authenticate(self.member)
        response = self.client.patch(self.url, {'status': 'in-progress'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in-progress')
        self.assertEqual(self.task.title, 'Test Task')

    def test_patch_task_changing_board_returns_400(self):
        other_board = self.make_board(self.owner, [self.member])
        self.authenticate(self.member)
        response = self.client.patch(self.url, {'board': other_board.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.task.refresh_from_db()
        self.assertEqual(self.task.board, self.board)

    def test_patch_task_with_unchanged_board_is_accepted(self):
        self.authenticate(self.member)
        response = self.client.patch(
            self.url, {'board': self.board.id, 'status': 'review'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_task_invalid_status_returns_400(self):
        self.authenticate(self.member)
        response = self.client.patch(self.url, {'status': 'to_do'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_task_assignee_not_board_member_returns_400(self):
        self.authenticate(self.member)
        response = self.client.patch(self.url, {'assignee_id': self.outsider.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_task_non_member_returns_403(self):
        self.authenticate(self.outsider)
        response = self.client.patch(self.url, {'status': 'done'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_task_not_found(self):
        self.authenticate(self.member)
        url = reverse('task-detail', kwargs={'task_id': 99999})
        response = self.client.patch(url, {'status': 'done'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_task_unauthenticated_returns_401(self):
        response = self.client.patch(self.url, {'status': 'done'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_and_put_are_not_part_of_the_api(self):
        self.authenticate(self.member)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            self.client.put(self.url, {'title': 'x'}, format='json').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_delete_task_as_creator(self):
        self.authenticate(self.creator)
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_delete_task_as_board_owner(self):
        self.authenticate(self.owner)
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_task_as_other_member_returns_403(self):
        self.authenticate(self.member)
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_delete_task_as_outsider_returns_403(self):
        self.authenticate(self.outsider)
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_task_not_found(self):
        self.authenticate(self.owner)
        url = reverse('task-detail', kwargs={'task_id': 99999})
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_task_removes_comments(self):
        comment = Comment.objects.create(task=self.task, author=self.member, content='x')
        self.authenticate(self.owner)
        self.client.delete(self.url)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_delete_task_unauthenticated_returns_401(self):
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_401_UNAUTHORIZED)


class DashboardTasksApiTest(ApiTestBase):

    def setUp(self):
        self.user = self.make_user('dash', 'Dana', 'Dash')
        self.other = self.make_user('other', 'Otto', 'Other')
        self.board = self.make_board(self.other, [self.user])
        self.assigned = self.make_task(
            self.board, self.other, title='Mine', assignee=self.user
        )
        self.reviewed = self.make_task(
            self.board, self.other, title='To review', reviewer=self.user
        )
        self.make_task(self.board, self.other, title='Not mine', assignee=self.other)
        self.authenticate(self.user)

    def test_assigned_to_me(self):
        response = self.client.get(reverse('tasks-assigned-to-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([t['id'] for t in response.data], [self.assigned.id])
        self.assertEqual(set(response.data[0].keys()), TASK_KEYS)
        self.assertEqual(set(response.data[0]['assignee'].keys()), USER_KEYS)

    def test_reviewing(self):
        response = self.client.get(reverse('tasks-reviewing'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([t['id'] for t in response.data], [self.reviewed.id])
        self.assertEqual(set(response.data[0].keys()), TASK_KEYS)

    def test_dashboard_endpoints_require_authentication(self):
        self.client.credentials()
        for name in ('tasks-assigned-to-me', 'tasks-reviewing'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CommentApiTest(ApiTestBase):

    def setUp(self):
        self.owner = self.make_user('owner', 'Olivia', 'Owner')
        self.author = self.make_user('author', 'Anna', 'Author')
        self.member = self.make_user('member', 'Mike', 'Member')
        self.outsider = self.make_user('outsider')
        self.board = self.make_board(self.owner, [self.author, self.member])
        self.task = self.make_task(self.board, self.owner)
        self.list_url = reverse('task-comments', kwargs={'task_id': self.task.id})

    def detail_url(self, comment, task=None):
        task = task or self.task
        return reverse(
            'task-comment-detail', kwargs={'task_id': task.id, 'comment_id': comment.id}
        )

    def test_create_comment(self):
        self.authenticate(self.author)
        response = self.client.post(self.list_url, {'content': 'New comment'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), COMMENT_KEYS)
        self.assertEqual(response.data['author'], 'Anna Author')
        self.assertEqual(response.data['content'], 'New comment')

    def test_create_comment_blank_content_returns_400(self):
        self.authenticate(self.author)
        response = self.client.post(self.list_url, {'content': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_comment_non_member_returns_403(self):
        self.authenticate(self.outsider)
        response = self.client.post(self.list_url, {'content': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_comment_task_not_found(self):
        self.authenticate(self.author)
        url = reverse('task-comments', kwargs={'task_id': 99999})
        self.assertEqual(
            self.client.post(url, {'content': 'x'}, format='json').status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_create_comment_unauthenticated_returns_401(self):
        response = self.client.post(self.list_url, {'content': 'x'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_comments_oldest_first(self):
        first = Comment.objects.create(task=self.task, author=self.author, content='first')
        second = Comment.objects.create(task=self.task, author=self.member, content='second')
        self.authenticate(self.member)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([c['id'] for c in response.data], [first.id, second.id])
        for entry in response.data:
            self.assertEqual(set(entry.keys()), COMMENT_KEYS)

    def test_list_comments_non_member_returns_403(self):
        self.authenticate(self.outsider)
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_403_FORBIDDEN)

    def test_list_comments_task_not_found(self):
        self.authenticate(self.author)
        url = reverse('task-comments', kwargs={'task_id': 99999})
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_comment_as_author(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='x')
        self.authenticate(self.author)
        response = self.client.delete(self.detail_url(comment))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_delete_comment_as_board_owner_returns_403(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='x')
        self.authenticate(self.owner)
        self.assertEqual(
            self.client.delete(self.detail_url(comment)).status_code, status.HTTP_403_FORBIDDEN
        )
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_delete_comment_as_other_member_returns_403(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='x')
        self.authenticate(self.member)
        self.assertEqual(
            self.client.delete(self.detail_url(comment)).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_delete_comment_not_found(self):
        self.authenticate(self.author)
        url = reverse('task-comment-detail', kwargs={'task_id': self.task.id, 'comment_id': 99999})
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_comment_with_wrong_task_returns_404(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='x')
        other_task = self.make_task(self.board, self.owner, title='Other')
        self.authenticate(self.author)
        response = self.client.delete(self.detail_url(comment, task=other_task))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_comment_task_not_found(self):
        self.authenticate(self.author)
        url = reverse('task-comment-detail', kwargs={'task_id': 99999, 'comment_id': 1})
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_comment_unauthenticated_returns_401(self):
        comment = Comment.objects.create(task=self.task, author=self.author, content='x')
        self.assertEqual(
            self.client.delete(self.detail_url(comment)).status_code,
            status.HTTP_401_UNAUTHORIZED
        )


class EndpointDocumentationTest(ApiTestBase):
    """
    The API must expose exactly the endpoints of the endpoint documentation.
    """

    def test_documented_paths_resolve(self):
        paths = [
            '/api/registration/', '/api/login/', '/api/email-check/',
            '/api/boards/', '/api/boards/1/',
            '/api/tasks/assigned-to-me/', '/api/tasks/reviewing/',
            '/api/tasks/', '/api/tasks/1/',
            '/api/tasks/1/comments/', '/api/tasks/1/comments/1/',
        ]
        self.authenticate(self.make_user('docs'))
        for path in paths:
            response = self.client.options(path)
            self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND, path)

    def test_undocumented_paths_do_not_exist(self):
        paths = [
            '/api/auth/register/', '/api/auth/login/', '/api/auth/logout/',
            '/api/auth/user/', '/api/contacts/', '/api/contacts/1/',
            '/api/subtasks/', '/api/subtasks/1/',
        ]
        self.authenticate(self.make_user('docs'))
        for path in paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, path)


class ErrorHandlingApiTest(ApiTestBase):

    def test_unauthenticated_request_returns_401_with_detail(self):
        response = self.client.get(reverse('board-list-create'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_not_found_returns_404_with_detail(self):
        self.authenticate(self.make_user('errors'))
        response = self.client.get(reverse('board-detail', kwargs={'board_id': 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

    def test_custom_exception_handler_handles_500(self):
        from .exceptions import custom_exception_handler
        response = custom_exception_handler(Exception('Unexpected internal error'), {})
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
            reverse('board-list-create'),
            HTTP_ORIGIN='http://localhost:3000',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_cors_headers_present_on_get(self):
        response = self.client.get(
            reverse('board-list-create'), HTTP_ORIGIN='http://localhost:3000'
        )
        self.assertEqual(
            response.headers['Access-Control-Allow-Origin'], 'http://localhost:3000'
        )


class AuthHeaderIntegrationTest(ApiTestBase):
    """
    Tests for flexible auth headers (Bearer, Token, case-insensitive, error handling).
    """

    def setUp(self):
        self.user = self.make_user('authheader')
        self.token = Token.objects.create(user=self.user)
        self.url = reverse('board-list-create')

    def test_accepted_header_prefixes(self):
        for prefix in ('Bearer', 'bearer', 'Token', 'token'):
            response = self.client.get(self.url, HTTP_AUTHORIZATION=f'{prefix} {self.token.key}')
            self.assertEqual(response.status_code, status.HTTP_200_OK, prefix)

    def test_malformed_auth_header_empty(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_malformed_auth_header_extra_parts(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer part1 part2')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_returns_401(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION='Bearer non_existent_token')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SwaggerApiDocumentationTest(APITestCase):
    """
    Tests for OpenAPI schema and Swagger UI endpoints.
    """

    def test_schema_endpoint_returns_200(self):
        self.assertEqual(self.client.get(reverse('schema')).status_code, status.HTTP_200_OK)

    def test_swagger_ui_endpoint_returns_200(self):
        self.assertEqual(self.client.get(reverse('swagger-ui')).status_code, status.HTTP_200_OK)

    def test_redoc_endpoint_returns_200(self):
        self.assertEqual(self.client.get(reverse('redoc')).status_code, status.HTTP_200_OK)
