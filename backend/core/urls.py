from django.urls import path
from .views import RegistrationView

urlpatterns = [
    path('auth/register/', RegistrationView.as_view(), name='register'),
]
