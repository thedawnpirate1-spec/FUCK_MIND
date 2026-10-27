from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Board, Task, Comment

User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    """
    Minimal user representation: id, email and full name.
    """
    fullname = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class AuthResponseSerializer(serializers.Serializer):
    """
    Documents the response of the registration and login endpoints.
    """
    token = serializers.CharField()
    fullname = serializers.CharField()
    email = serializers.EmailField()
    user_id = serializers.IntegerField()


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration (fullname, email, password, repeated_password).
    """
    fullname = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {'repeated_password': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        first_name, _, last_name = validated_data['fullname'].strip().partition(' ')
        return User.objects.create_user(
            username=self._unique_username(validated_data['email']),
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name.strip()
        )

    @staticmethod
    def _unique_username(email):
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        return username


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login via email and password.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user_obj = User.objects.filter(email__iexact=attrs['email'].strip()).first()
        user = user_obj and authenticate(
            username=user_obj.username, password=attrs['password']
        )
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        attrs['user'] = user
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    """
    Task representation used for creation and for the dashboard lists
    (assigned-to-me, reviewing). Assignee and reviewer are written via
    `assignee_id` / `reviewer_id` and read as nested user summaries.
    """
    board = serializers.PrimaryKeyRelatedField(queryset=Board.objects.all())
    assignee = UserSummarySerializer(read_only=True)
    reviewer = UserSummarySerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='assignee',
        write_only=True, required=False, allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='reviewer',
        write_only=True, required=False, allow_null=True
    )
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority',
            'assignee', 'assignee_id', 'reviewer', 'reviewer_id',
            'due_date', 'comments_count'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        board = attrs.get('board') or self.instance.board
        for field in ('assignee', 'reviewer'):
            user = attrs.get(field)
            if user and not board.is_member_or_owner(user):
                raise serializers.ValidationError(
                    {f'{field}_id': 'The user must be a member of the board.'}
                )
        return attrs


class TaskUpdateSerializer(TaskSerializer):
    """
    Serializer for PATCH /api/tasks/{task_id}/. The board of a task cannot
    be changed, and the response contains neither `board` nor `comments_count`.
    """
    board = None
    comments_count = None

    class Meta(TaskSerializer.Meta):
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'assignee_id', 'reviewer', 'reviewer_id', 'due_date'
        ]

    def validate(self, attrs):
        board_value = self.initial_data.get('board')
        if board_value is not None and str(board_value) != str(self.instance.board_id):
            raise serializers.ValidationError(
                {'board': 'Changing the board of a task is not allowed.'}
            )
        return super().validate(attrs)


class BoardTaskSerializer(TaskSerializer):
    """
    Read-only task representation nested inside the board detail response.
    """
    board = None

    class Meta(TaskSerializer.Meta):
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'due_date', 'comments_count'
        ]


class BoardSerializer(serializers.ModelSerializer):
    """
    Board representation for GET/POST /api/boards/: summary counters and
    `owner_id`. Members are only accepted as a list of user ids on input.
    """
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True, required=False
    )
    owner_id = serializers.IntegerField(read_only=True)
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'members', 'member_count', 'ticket_count',
            'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id'
        ]
        read_only_fields = ['id']

    def get_member_count(self, obj) -> int:
        return obj.members.count()

    def get_ticket_count(self, obj) -> int:
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj) -> int:
        return obj.tasks.filter(status='to-do').count()

    def get_tasks_high_prio_count(self, obj) -> int:
        return obj.tasks.filter(priority='high').count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Board representation for GET /api/boards/{board_id}/ including members and tasks.
    """
    owner_id = serializers.IntegerField(read_only=True)
    members = UserSummarySerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for PATCH /api/boards/{board_id}/. Members are sent as a list of
    user ids and replace the current member list; the response contains
    `owner_data` and `members_data`.
    """
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True, required=False
    )
    owner_data = UserSummarySerializer(source='owner', read_only=True)
    members_data = UserSummarySerializer(source='members', many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'members', 'owner_data', 'members_data']
        read_only_fields = ['id']


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments; the author is exposed as full name.
    """
    author = serializers.CharField(source='author.fullname', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
        read_only_fields = ['id', 'created_at']
