from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Erweitertes User-Modell für KanMind.
    """
    email = models.EmailField(unique=True)
    color = models.CharField(max_length=7, default='#FF7A00', help_text="Hex color for user badge")

    @property
    def fullname(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username

    def __str__(self):
        return f"{self.username} ({self.email})"


class Contact(models.Model):
    """
    Kontakt-Modell für KanMind Board-Assignees.
    """
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, default='')
    color = models.CharField(max_length=7, default='#FF7A00')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Board(models.Model):
    """
    Board-Modell zur Gruppierung von Tasks und Mitgliedern.
    """
    title = models.CharField(max_length=150)
    members = models.ManyToManyField(CustomUser, related_name='boards', blank=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_boards', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Task(models.Model):
    """
    Task-Modell für KanMind Kanban Board.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('to_do', 'To Do'),
        ('to-do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('in-progress', 'In Progress'),
        ('await_feedback', 'Await Feedback'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to_do')
    category = models.CharField(max_length=100, blank=True, default='User Story')
    assignee = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    reviewer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewing_tasks')
    assigned_to = models.ManyToManyField(Contact, blank=True, related_name='tasks')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def comments_count(self):
        return self.comments.count()

    def __str__(self):
        return f"{self.title} [{self.status}]"


class Subtask(models.Model):
    """
    Subtask-Modell für KanMind Tasks.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (Done: {self.is_completed})"


class Comment(models.Model):
    """
    Kommentar-Modell für Diskussionen innerhalb von Tasks.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"
