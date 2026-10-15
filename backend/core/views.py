from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import Contact, Task, Subtask, Board, Comment
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    UserDetailSerializer,
    ContactSerializer,
    TaskSerializer,
    SubtaskSerializer,
    BoardSerializer,
    CommentSerializer
)

User = get_user_model()


class RegistrationView(APIView):
    """
    Endpunkt für die Registrierung neuer Benutzer.
    Erstellt den Benutzer und liefert direkt einen Auth-Token zurück.
    """
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    @extend_schema(responses={201: RegistrationSerializer})
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email,
                'fullname': user.fullname
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Endpunkt für den Login via Username/E-Mail & Passwort.
    Liefert bei Erfolg den Token und Benutzerdaten zurück.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(responses={200: UserDetailSerializer})
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
                'fullname': user.fullname,
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

    @extend_schema(request=None, responses={200: OpenApiResponse(description='Erfolgreich abgemeldet.')})
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
    serializer_class = UserDetailSerializer

    @extend_schema(responses={200: UserDetailSerializer})
    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmailCheckView(APIView):
    """
    Endpunkt zur Überprüfung von E-Mail-Adressen für Board-Einladungen.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserDetailSerializer})
    def get(self, request):
        email = request.query_params.get('email', '').strip()
        if not email:
            return Response({'detail': 'E-Mail-Adresse fehlt.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email__iexact=email)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'detail': 'Benutzer nicht gefunden.'}, status=status.HTTP_404_NOT_FOUND)


class BoardListCreateView(generics.ListCreateAPIView):
    """
    GET: Liste aller Boards des angemeldeten Benutzers abrufen.
    POST: Ein neues Board anlegen.
    """
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Board.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        board = serializer.save(owner=self.request.user)
        board.members.add(self.request.user)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PATCH, PUT, DELETE für ein einzelnes Board.
    """
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]


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
    GET: Liste aller Tasks abrufen mit Unterstützung für Query-Parameter.
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
        board_param = self.request.query_params.get('board')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if priority_param:
            queryset = queryset.filter(priority=priority_param)
        if assigned_to_param:
            queryset = queryset.filter(assigned_to__id=assigned_to_param)
        if board_param:
            queryset = queryset.filter(board_id=board_param)
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
    PUT / PATCH: Task bearbeiten.
    DELETE: Task löschen.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]


class AssignedTasksView(generics.ListAPIView):
    """
    GET: Liste aller Tasks abrufen, die dem angemeldeten Benutzer zugewiesen sind.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user).order_by('-created_at')


class ReviewingTasksView(generics.ListAPIView):
    """
    GET: Liste aller Tasks abrufen, bei denen der angemeldete Benutzer Reviewer ist.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user).order_by('-created_at')


class TaskCommentListCreateView(generics.ListCreateAPIView):
    """
    GET: Kommentare eines Tasks abrufen.
    POST: Neuen Kommentar zu einem Task verfassen.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs.get('task_id')
        return Comment.objects.filter(task_id=task_id).order_by('created_at')

    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_id')
        task = generics.get_object_or_404(Task, id=task_id)
        serializer.save(author=self.request.user, task=task)


class TaskCommentDetailView(generics.DestroyAPIView):
    """
    DELETE: Einzelnen Kommentar eines Tasks löschen.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs.get('task_id')
        return Comment.objects.filter(task_id=task_id)


class SubtaskListCreateView(generics.ListCreateAPIView):
    """
    GET: Subtasks abrufen (optional filterbar per ?task=<task_id>).
    POST: Einen neuen Subtask für eine Task erstellen.
    """
    serializer_class = SubtaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Subtask.objects.all().order_by('created_at')
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        return queryset


class SubtaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Details eines Subtasks abrufen.
    PUT / PATCH: Subtask bearbeiten (z.B. Checkbox is_completed toggeln).
    DELETE: Subtask löschen.
    """
    queryset = Subtask.objects.all()
    serializer_class = SubtaskSerializer
    permission_classes = [IsAuthenticated]


def custom_404_view(request, exception=None):
    """
    Globaler 404-Handler für nicht gefundene Routen.
    """
    from django.http import JsonResponse
    return JsonResponse({'detail': 'Die angeforderte Ressource wurde nicht gefunden.'}, status=404)


def custom_500_view(request):
    """
    Globaler 500-Handler für Serverfehler.
    """
    from django.http import JsonResponse
    return JsonResponse({'detail': 'Ein interner Serverfehler ist aufgetreten.'}, status=500)
