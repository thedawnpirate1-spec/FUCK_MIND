from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework import generics, permissions, exceptions
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
    BoardTaskSerializer,
    SubtaskSerializer,
    BoardSerializer,
    CommentSerializer
)

User = get_user_model()


class RegistrationView(APIView):
    """
    Endpoint for user registration.
    Creates user and returns authentication token.
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
    Endpoint for user login via username/email and password.
    Returns auth token and user profile data on success.
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
    Endpoint for user logout and token deletion.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: OpenApiResponse(description='Successfully logged out.')}
    )
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """
    Protected endpoint to retrieve profile details of the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    @extend_schema(responses={200: UserDetailSerializer})
    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmailCheckView(APIView):
    """
    Endpoint to check email address availability for board invitations.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserDetailSerializer})
    def get(self, request):
        email = request.query_params.get('email', '').strip()
        if not email:
            return Response(
                {'detail': 'Email parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email__iexact=email)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class IsBoardMemberOrOwner(permissions.BasePermission):
    """
    Berechtigungsprüfung für Boards: Nur Mitglieder oder Eigentümer dürfen zugreifen.
    """
    def has_object_permission(self, request, view, obj):
        is_owner = (obj.owner == request.user)
        is_member = obj.members.filter(id=request.user.id).exists()
        if request.method == 'DELETE':
            return is_owner
        return is_owner or is_member


class BoardListCreateView(generics.ListCreateAPIView):
    """
    GET: Alle Boards des Nutzers auflisten.
    POST: Neues Board erstellen.
    """
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Board.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        board = serializer.save(owner=self.request.user)
        if not board.members.filter(id=self.request.user.id).exists():
            board.members.add(self.request.user)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PATCH, PUT, DELETE für ein einzelnes Board.
    """
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner]


class ContactListCreateView(generics.ListCreateAPIView):
    """
    GET: List all contacts.
    POST: Create a new contact.
    """
    queryset = Contact.objects.all().order_by('name')
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE for a single contact.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]


class TaskListCreateView(generics.ListCreateAPIView):
    """
    GET: Tasks auflisten (mit Filtern für Status, Priorität, Board etc.).
    POST: Neuen Task erstellen.
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
            try:
                board = Board.objects.get(id=board_param)
            except (Board.DoesNotExist, ValueError):
                raise exceptions.NotFound({'detail': 'Board not found.'})
            is_member = board.members.filter(id=self.request.user.id).exists()
            is_owner = (board.owner == self.request.user)
            if not (is_owner or is_member):
                raise exceptions.PermissionDenied(
                    {'detail': 'You are not a member of this board.'}
                )
            queryset = queryset.filter(board=board)
        if search_param:
            queryset = queryset.filter(
                Q(title__icontains=search_param) | Q(description__icontains=search_param)
            )
        return queryset

    def create(self, request, *args, **kwargs):
        board_id = request.data.get('board') if request.data.get('board') is not None else request.data.get('board_id')
        if isinstance(board_id, dict):
            board_id = board_id.get('id')
        if board_id is not None:
            try:
                board = Board.objects.get(id=board_id)
            except (Board.DoesNotExist, ValueError, TypeError):
                return Response(
                    {'detail': 'Board not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            is_member = board.members.filter(id=request.user.id).exists()
            is_owner = (board.owner == request.user)
            if not (is_owner or is_member):
                return Response(
                    {'detail': 'You are not a member of this board.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE für einen einzelnen Task.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        task_id = self.kwargs.get('pk')
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise exceptions.NotFound({'detail': 'Task not found.'})

        if task.board:
            is_board_owner = (task.board.owner == self.request.user)
            is_board_member = task.board.members.filter(id=self.request.user.id).exists()
            if not (is_board_owner or is_board_member):
                raise exceptions.PermissionDenied(
                    {'detail': 'You do not have permission to access this task.'}
                )
        return task

    def update(self, request, *args, **kwargs):
        board_id = request.data.get('board') if request.data.get('board') is not None else request.data.get('board_id')
        if isinstance(board_id, dict):
            board_id = board_id.get('id')
        if board_id is not None:
            try:
                board = Board.objects.get(id=board_id)
            except (Board.DoesNotExist, ValueError, TypeError):
                return Response(
                    {'detail': 'Board not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            is_member = board.members.filter(id=request.user.id).exists()
            is_owner = (board.owner == request.user)
            if not (is_owner or is_member):
                return Response(
                    {'detail': 'You are not a member of this board.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().update(request, *args, **kwargs)


class AssignedTasksView(generics.ListAPIView):
    """
    GET: List all tasks assigned to the authenticated user.
    """
    serializer_class = BoardTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user).order_by('-created_at')


class ReviewingTasksView(generics.ListAPIView):
    """
    GET: List all tasks where the authenticated user is reviewer.
    """
    serializer_class = BoardTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user).order_by('-created_at')


class TaskCommentListCreateView(generics.ListCreateAPIView):
    """
    GET: Kommentare eines Tasks abrufen.
    POST: Neuen Kommentar zu einem Task erstellen.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_task(self):
        task_id = self.kwargs.get('task_id')
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise exceptions.NotFound({'detail': 'Task not found.'})

        if task.board:
            is_member = task.board.members.filter(id=self.request.user.id).exists()
            is_owner = (task.board.owner == self.request.user)
            if not (is_owner or is_member):
                raise exceptions.PermissionDenied(
                    {'detail': 'You do not have permission to access comments for this task.'}
                )
        return task

    def get_queryset(self):
        task = self.get_task()
        return Comment.objects.filter(task=task).order_by('created_at')

    def perform_create(self, serializer):
        task = self.get_task()
        serializer.save(author=self.request.user, task=task)


class TaskCommentDetailView(generics.DestroyAPIView):
    """
    DELETE: Einzelnen Kommentar eines Tasks löschen.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        task_id = self.kwargs.get('task_id')
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise exceptions.NotFound({'detail': 'Task not found.'})

        if task.board:
            is_board_owner = (task.board.owner == self.request.user)
            is_board_member = task.board.members.filter(id=self.request.user.id).exists()
            if not (is_board_owner or is_board_member):
                raise exceptions.PermissionDenied(
                    {'detail': 'You do not have permission to access this task.'}
                )
        else:
            is_board_owner = False

        try:
            comment = Comment.objects.get(id=self.kwargs.get('pk'), task=task)
        except Comment.DoesNotExist:
            raise exceptions.NotFound({'detail': 'Comment not found.'})

        if comment.author != self.request.user and not is_board_owner:
            raise exceptions.PermissionDenied(
                {'detail': 'You do not have permission to delete this comment.'}
            )

        return comment


class SubtaskListCreateView(generics.ListCreateAPIView):
    """
    GET: Subtasks abrufen (filterbar nach ?task=<task_id>).
    POST: Neuen Subtask erstellen.
    """
    serializer_class = SubtaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Subtask.objects.all().order_by('created_at')
        task_id = self.request.query_params.get('task')
        if task_id:
            try:
                task = Task.objects.get(id=task_id)
                if task.board:
                    is_member = task.board.members.filter(id=self.request.user.id).exists()
                    is_owner = (task.board.owner == self.request.user)
                    if not (is_owner or is_member):
                        raise exceptions.PermissionDenied(
                            {'detail': 'You do not have permission to view subtasks for this task.'}
                        )
            except Task.DoesNotExist:
                raise exceptions.NotFound({'detail': 'Task not found.'})
            queryset = queryset.filter(task_id=task_id)
        return queryset

    def perform_create(self, serializer):
        task = serializer.validated_data.get('task')
        if task and task.board:
            is_member = task.board.members.filter(id=self.request.user.id).exists()
            is_owner = (task.board.owner == self.request.user)
            if not (is_owner or is_member):
                raise exceptions.PermissionDenied(
                    {'detail': 'You do not have permission to create subtasks for this task.'}
                )
        serializer.save()


class SubtaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE für einen einzelnen Subtask.
    """
    queryset = Subtask.objects.all()
    serializer_class = SubtaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        subtask = super().get_object()
        if subtask.task and subtask.task.board:
            is_member = subtask.task.board.members.filter(id=self.request.user.id).exists()
            is_owner = (subtask.task.board.owner == self.request.user)
            if not (is_owner or is_member):
                raise exceptions.PermissionDenied(
                    {'detail': 'You do not have permission to access this subtask.'}
                )
        return subtask


def custom_404_view(request, exception=None):
    """
    Global 404 handler for unknown routes.
    """
    from django.http import JsonResponse
    return JsonResponse({'detail': 'The requested resource was not found.'}, status=404)


def custom_500_view(request):
    """
    Global 500 handler for unhandled server errors.
    """
    from django.http import JsonResponse
    return JsonResponse({'detail': 'An internal server error occurred.'}, status=500)
