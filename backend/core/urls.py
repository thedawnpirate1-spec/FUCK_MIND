from django.urls import path
from .views import (
    RegistrationView,
    LoginView,
    LogoutView,
    UserProfileView,
    EmailCheckView,
    BoardListCreateView,
    BoardDetailView,
    AssignedTasksView,
    ReviewingTasksView,
    TaskCommentListCreateView,
    TaskCommentDetailView,
    ContactListCreateView,
    ContactDetailView,
    TaskListCreateView,
    TaskDetailView,
    SubtaskListCreateView,
    SubtaskDetailView
)

urlpatterns = [
    # Authentifizierung & Benutzer
    path('auth/register/', RegistrationView.as_view(), name='register'),
    path('registration/', RegistrationView.as_view(), name='registration-frontend'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('login/', LoginView.as_view(), name='login-frontend'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/user/', UserProfileView.as_view(), name='user-profile'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),

    # Boards
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:pk>/', BoardDetailView.as_view(), name='board-detail'),

    # Tasks Dashboard & Kommentare
    path('tasks/assigned-to-me/', AssignedTasksView.as_view(), name='tasks-assigned-to-me'),
    path('tasks/reviewing/', ReviewingTasksView.as_view(), name='tasks-reviewing'),
    path('tasks/<int:task_id>/comments/', TaskCommentListCreateView.as_view(), name='task-comments'),
    path('tasks/<int:task_id>/comments/<int:pk>/', TaskCommentDetailView.as_view(), name='task-comment-detail'),

    # Kontakte, Tasks & Subtasks
    path('contacts/', ContactListCreateView.as_view(), name='contact-list-create'),
    path('contacts/<int:pk>/', ContactDetailView.as_view(), name='contact-detail'),
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('subtasks/', SubtaskListCreateView.as_view(), name='subtask-list-create'),
    path('subtasks/<int:pk>/', SubtaskDetailView.as_view(), name='subtask-detail'),
]
