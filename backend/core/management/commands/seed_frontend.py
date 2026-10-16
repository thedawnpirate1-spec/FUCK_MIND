from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Board, Task, Comment

User = get_user_model()


class Command(BaseCommand):
    """
    Erstellt Demo-Daten für das Frontend inklusive Gast-Account.
    """
    help = 'Erstellt Demo-Daten für das Frontend inklusive Gast-Account'

    def handle(self, *args, **options):
        guest_user, created = User.objects.get_or_create(
            email='kevin@kovacsi.de',
            defaults={
                'username': 'kevin',
                'first_name': 'Kevin',
                'last_name': 'Kovacsi',
                'color': '#FF7A00'
            }
        )
        guest_user.set_password('asdasdasd')
        guest_user.save()

        colleague_user, _ = User.objects.get_or_create(
            email='erika@example.com',
            defaults={
                'username': 'erika',
                'first_name': 'Erika',
                'last_name': 'Mustermann',
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
            title='Frontend an REST API anbinden',
            defaults={
                'description': 'Integration der Backend-Endpunkte für Boards, Tasks und Auth',
                'status': 'in-progress',
                'priority': 'high',
                'category': 'User Story',
                'assignee': guest_user,
                'reviewer': colleague_user,
                'due_date': today + timedelta(days=3),
                'created_by': guest_user
            }
        )

        task2, _ = Task.objects.get_or_create(
            board=board,
            title='Swagger & OpenAPI Doku verifizieren',
            defaults={
                'description': 'Alle Endpunkte in der Swagger UI testen',
                'status': 'done',
                'priority': 'medium',
                'category': 'Technical Task',
                'assignee': guest_user,
                'due_date': today - timedelta(days=1),
                'created_by': guest_user
            }
        )

        task3, _ = Task.objects.get_or_create(
            board=board,
            title='UI Feedback und Review',
            defaults={
                'description': 'Board-Design und Responsiveness auf verschiedenen Geräten prüfen',
                'status': 'to-do',
                'priority': 'low',
                'category': 'User Story',
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
                content='Die Authentifizierung und Boards funktionieren schon einwandfrei!'
            )

        self.stdout.write(self.style.SUCCESS('Erfolgreich Testdaten für das Frontend initialisiert.'))
