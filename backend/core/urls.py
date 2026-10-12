from django.urls import path
from .views import (
    RegistrationView,
    LoginView,
    LogoutView,
    UserProfileView,
    ContactListCreateView,
    ContactDetailView,
    TaskListCreateView,
    TaskDetailView,
    SubtaskListCreateView,
    SubtaskDetailView
)

urlpatterns = [
    path('auth/register/', RegistrationView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/user/', UserProfileView.as_view(), name='user-profile'),
    path('contacts/', ContactListCreateView.as_view(), name='contact-list-create'),
    path('contacts/<int:pk>/', ContactDetailView.as_view(), name='contact-detail'),
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('subtasks/', SubtaskListCreateView.as_view(), name='subtask-list-create'),
    path('subtasks/<int:pk>/', SubtaskDetailView.as_view(), name='subtask-detail'),
]


