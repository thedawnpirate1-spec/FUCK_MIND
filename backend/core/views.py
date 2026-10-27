from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import exceptions, generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Board, Comment, Task
from .serializers import (
    AuthResponseSerializer,
    BoardDetailSerializer,
    BoardSerializer,
    BoardUpdateSerializer,
    CommentSerializer,
    LoginSerializer,
    RegistrationSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
    UserSummarySerializer,
)

User = get_user_model()


def build_auth_response(user):
    """
    Returns the auth payload (token, fullname, email, user_id) for a user.
    """
    token, _ = Token.objects.get_or_create(user=user)
    return {
        'token': token.key,
        'fullname': user.fullname,
        'email': user.email,
        'user_id': user.pk,
    }


class RegistrationView(APIView):
    """
    POST /api/registration/ - creates a user and returns token and user data.
    """
    permission_classes = [AllowAny]

    @extend_schema(request=RegistrationSerializer, responses={201: AuthResponseSerializer})
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(build_auth_response(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/login/ - authenticates via email and password, returns token and user data.
    """
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: AuthResponseSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(build_auth_response(user), status=status.HTTP_200_OK)


class EmailCheckView(APIView):
    """
    GET /api/email-check/?email=... - returns the user registered with this email.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter('email', str, required=True)],
        responses={200: UserSummarySerializer}
    )
    def get(self, request):
        email = request.query_params.get('email', '').strip()
        try:
            validate_email(email)
        except DjangoValidationError:
            return Response(
                {'detail': 'A valid email address is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            return Response({'detail': 'Email not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSummarySerializer(user).data, status=status.HTTP_200_OK)


class IsBoardMemberOrOwner(permissions.BasePermission):
    """
    Members and the owner may read and update a board, only the owner may delete it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return obj.owner_id == request.user.id
        return obj.is_member_or_owner(request.user)


class BoardListCreateView(generics.ListCreateAPIView):
    """
    GET: boards the user owns or is a member of.
    POST: create a board; the requesting user becomes the owner.
    """
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Board.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: board with members and tasks.
    PATCH: update title and members.
    DELETE: delete the board (owner only).
    """
    queryset = Board.objects.all()
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner]
    lookup_url_kwarg = 'board_id'
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return BoardUpdateSerializer
        return BoardDetailSerializer


class IsTaskBoardMember(permissions.BasePermission):
    """
    Board members may update a task; only its creator or the board owner may delete it.
    """
    def has_object_permission(self, request, view, obj):
        board = obj.board
        if board is None:
            return False
        if request.method == 'DELETE':
            return obj.created_by_id == request.user.id or board.owner_id == request.user.id
        return board.is_member_or_owner(request.user)


class TaskCreateView(generics.CreateAPIView):
    """
    POST /api/tasks/ - creates a task inside a board the user belongs to.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        board_id = request.data.get('board')
        if board_id is not None:
            try:
                board = Board.objects.get(pk=board_id)
            except Board.DoesNotExist:
                raise exceptions.NotFound({'detail': 'Board not found.'})
            except (TypeError, ValueError):
                board = None  # malformed id: the serializer answers with 400
            if board and not board.is_member_or_owner(request.user):
                raise exceptions.PermissionDenied(
                    {'detail': 'You must be a member of the board to create a task.'}
                )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    PATCH: update a task (board members only).
    DELETE: delete a task (task creator or board owner only).
    """
    queryset = Task.objects.select_related('board')
    serializer_class = TaskUpdateSerializer
    permission_classes = [IsAuthenticated, IsTaskBoardMember]
    lookup_url_kwarg = 'task_id'
    http_method_names = ['patch', 'delete', 'options']


class AssignedTasksView(generics.ListAPIView):
    """
    GET /api/tasks/assigned-to-me/ - tasks where the user is the assignee.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user).order_by('-created_at')


class ReviewingTasksView(generics.ListAPIView):
    """
    GET /api/tasks/reviewing/ - tasks where the user is the reviewer.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user).order_by('-created_at')


def get_task_or_404(task_id):
    try:
        return Task.objects.select_related('board').get(pk=task_id)
    except Task.DoesNotExist:
        raise exceptions.NotFound({'detail': 'Task not found.'})


class TaskCommentListCreateView(generics.ListCreateAPIView):
    """
    GET: comments of a task, oldest first.
    POST: add a comment; the author is the requesting user.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_task(self):
        task = get_task_or_404(self.kwargs['task_id'])
        if task.board is None or not task.board.is_member_or_owner(self.request.user):
            raise exceptions.PermissionDenied(
                {'detail': 'You must be a member of the board this task belongs to.'}
            )
        return task

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Comment.objects.none()
        return Comment.objects.filter(task=self.get_task()).select_related('author').order_by(
            'created_at'
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, task=self.get_task())


class TaskCommentDetailView(generics.DestroyAPIView):
    """
    DELETE /api/tasks/{task_id}/comments/{comment_id}/ - only the comment author may delete.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        task = get_task_or_404(self.kwargs['task_id'])
        try:
            comment = Comment.objects.select_related('author').get(
                pk=self.kwargs['comment_id'], task=task
            )
        except Comment.DoesNotExist:
            raise exceptions.NotFound({'detail': 'Comment not found.'})
        if comment.author_id != self.request.user.id:
            raise exceptions.PermissionDenied(
                {'detail': 'Only the author of a comment can delete it.'}
            )
        return comment


def custom_404_view(request, exception=None):
    """
    Global 404 handler for unknown routes.
    """
    return JsonResponse({'detail': 'The requested resource was not found.'}, status=404)


def custom_500_view(request):
    """
    Global 500 handler for unhandled server errors.
    """
    return JsonResponse({'detail': 'An internal server error occurred.'}, status=500)
