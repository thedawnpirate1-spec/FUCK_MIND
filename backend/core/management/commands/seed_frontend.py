from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Board, Task, Comment

User = get_user_model()


class Command(BaseCommand):
    """
    Populates demo data for testing including a guest account.
    """
    help = 'Populates demo data for testing including a guest account'

    def handle(self, *args, **options):
        guest_user, created = User.objects.get_or_create(
            email='guest@example.com',
            defaults={
                'username': 'guest',
                'first_name': 'Guest',
                'last_name': 'User',
                'color': '#FF7A00'
            }
        )
        guest_user.set_password('Password123!')
        guest_user.save()

        colleague_user, _ = User.objects.get_or_create(
            email='colleague@example.com',
            defaults={
                'username': 'colleague',
                'first_name': 'Colleague',
                'last_name': 'User',
                'color': '#9327FF'
            }
        )
        colleague_user.set_password('Password123!')
        colleague_user.save()

        board, _ = Board.objects.get_or_create(
            title='KanMind Development Board',
            defaults={'owner': guest_user}
        )
        board.members.add(guest_user, colleague_user)

        today = date.today()

        task1, _ = Task.objects.get_or_create(
            board=board,
            title='Connect frontend to REST API',
            defaults={
                'description': 'Integrate backend endpoints for boards, tasks, and auth',
                'status': 'in-progress',
                'priority': 'high',
                'assignee': guest_user,
                'reviewer': colleague_user,
                'due_date': today + timedelta(days=3),
                'created_by': guest_user
            }
        )

        task2, _ = Task.objects.get_or_create(
            board=board,
            title='Verify Swagger and OpenAPI documentation',
            defaults={
                'description': 'Test all endpoints in Swagger UI',
                'status': 'done',
                'priority': 'medium',
                'assignee': guest_user,
                'due_date': today - timedelta(days=1),
                'created_by': guest_user
            }
        )

        task3, _ = Task.objects.get_or_create(
            board=board,
            title='UI feedback and review',
            defaults={
                'description': 'Test board design and responsiveness across devices',
                'status': 'to-do',
                'priority': 'low',
                'assignee': colleague_user,
                'reviewer': guest_user,
                'due_date': today + timedelta(days=7),
                'created_by': guest_user
            }
        )

        if not task1.comments.exists():
            Comment.objects.create(
                task=task1,
                author=colleague_user,
                content='Authentication and boards are working properly.'
            )

        self.stdout.write(self.style.SUCCESS('Successfully initialized demo data.'))
