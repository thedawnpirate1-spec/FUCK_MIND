from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .models import Contact, Task
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    UserDetailSerializer,
    ContactSerializer,
    TaskSerializer
)


class RegistrationView(APIView):
    """
    Endpunkt für die Registrierung neuer Benutzer.
    Erstellt den Benutzer und liefert direkt einen Auth-Token zurück.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Endpunkt für den Login via Username/E-Mail & Passwort.
    Liefert bei Erfolg den Token und Benutzerdaten zurück.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'color': user.color
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Endpunkt für das Abmelden / Token-Inaktivieren.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'detail': 'Erfolgreich abgemeldet.'}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    Geschützter Endpunkt zum Abrufen der Daten des angemeldeten Benutzers.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContactListCreateView(generics.ListCreateAPIView):
    """
    GET: Liste aller Kontakte abrufen.
    POST: Einen neuen Kontakt erstellen.
    """
    queryset = Contact.objects.all().order_by('name')
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE für einzelne Kontakte.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]


class TaskListCreateView(generics.ListCreateAPIView):
    """
    GET: Liste aller Tasks abrufen mit Unterstüzung für Query-Parameter (status, priority, search, assigned_to).
    POST: Einen neuen Task erstellen.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.all().order_by('-created_at')
        status_param = self.request.query_params.get('status')
        priority_param = self.request.query_params.get('priority')
        search_param = self.request.query_params.get('search')
        assigned_to_param = self.request.query_params.get('assigned_to')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if priority_param:
            queryset = queryset.filter(priority=priority_param)
        if assigned_to_param:
            queryset = queryset.filter(assigned_to__id=assigned_to_param)
        if search_param:
            queryset = queryset.filter(
                Q(title__icontains=search_param) | Q(description__icontains=search_param)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Details eines einzelnen Tasks abrufen.
    PUT / PATCH: Task bearbeiten (z.B. Status-Drag&Drop oder Prioritätsänderung).
    DELETE: Task löschen.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

