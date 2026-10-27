from django.urls import path
from .views import (
    RegistrationView,
    LoginView,
    EmailCheckView,
    BoardListCreateView,
    BoardDetailView,
    AssignedTasksView,
    ReviewingTasksView,
    TaskCreateView,
    TaskDetailView,
    TaskCommentListCreateView,
    TaskCommentDetailView,
)

urlpatterns = [
    # Authentication & Users
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),

    # Boards
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:board_id>/', BoardDetailView.as_view(), name='board-detail'),

    # Tasks
    path('tasks/assigned-to-me/', AssignedTasksView.as_view(), name='tasks-assigned-to-me'),
    path('tasks/reviewing/', ReviewingTasksView.as_view(), name='tasks-reviewing'),
    path('tasks/', TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),

    # Comments
    path(
        'tasks/<int:task_id>/comments/',
        TaskCommentListCreateView.as_view(),
        name='task-comments'
    ),
    path(
        'tasks/<int:task_id>/comments/<int:comment_id>/',
        TaskCommentDetailView.as_view(),
        name='task-comment-detail'
    ),
]
