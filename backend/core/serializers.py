from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from .models import Contact, Task, Subtask, Board, Comment

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for authenticated user profile data.
    """
    user_id = serializers.IntegerField(source='id', read_only=True)
    fullname = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'user_id', 'id', 'username', 'email',
            'first_name', 'last_name', 'fullname', 'color'
        ]


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for contacts with automatic whitespace trimming.
    """
    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'phone', 'color', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        return value.strip()

    def validate_email(self, value):
        return value.strip().lower()


class SubtaskSerializer(serializers.ModelSerializer):
    """
    Serializer for subtasks, usable standalone or nested.
    """
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Subtask
        fields = ['id', 'task', 'title', 'is_completed', 'created_at']
        read_only_fields = ['created_at']
        extra_kwargs = {
            'task': {'required': False}
        }

    def validate(self, attrs):
        if not self.parent and 'task' not in attrs and not self.instance:
            raise serializers.ValidationError({"task": "This field is required."})
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for tasks including nested subtasks, assignees, and reviewers.
    """
    assigned_to_details = ContactSerializer(source='assigned_to', many=True, read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Contact.objects.all(), required=False
    )
    subtasks = SubtaskSerializer(many=True, required=False)
    assignee = UserDetailSerializer(read_only=True)
    reviewer = UserDetailSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assignee',
        required=False,
        allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='reviewer',
        required=False,
        allow_null=True
    )
    comments_count = serializers.IntegerField(read_only=True)
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'due_date', 'priority',
            'status', 'category', 'assigned_to', 'assigned_to_details',
            'assignee', 'assignee_id', 'reviewer', 'reviewer_id',
            'comments_count', 'subtasks', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        data_copy = data.copy() if hasattr(data, 'copy') else dict(data)

        if 'assigned_to' in data_copy and data_copy['assigned_to'] is None:
            data_copy['assigned_to'] = []

        if 'due_date' in data_copy and data_copy['due_date'] == '':
            data_copy['due_date'] = None

        if data_copy.get('assignee_id') in ['', 0]:
            data_copy['assignee_id'] = None

        if 'assignee' in data_copy:
            val = data_copy.pop('assignee')
            if isinstance(val, dict):
                data_copy['assignee_id'] = val.get('id')
            elif val not in ['', 0]:
                data_copy['assignee_id'] = val

        if data_copy.get('reviewer_id') in ['', 0]:
            data_copy['reviewer_id'] = None

        if 'reviewer' in data_copy:
            val = data_copy.pop('reviewer')
            if isinstance(val, dict):
                data_copy['reviewer_id'] = val.get('id')
            elif val not in ['', 0]:
                data_copy['reviewer_id'] = val

        if 'status' in data_copy and isinstance(data_copy['status'], str):
            data_copy['status'] = data_copy['status'].strip().lower().replace(' ', '_')

        if 'priority' in data_copy and isinstance(data_copy['priority'], str):
            data_copy['priority'] = data_copy['priority'].strip().lower()

        if 'subtasks' in data_copy and isinstance(data_copy['subtasks'], list):
            normalized_subtasks = []
            for item in data_copy['subtasks']:
                if isinstance(item, str):
                    normalized_subtasks.append({'title': item.strip()})
                elif isinstance(item, dict):
                    normalized_subtasks.append(item)
            data_copy['subtasks'] = normalized_subtasks

        return super().to_internal_value(data_copy)

    def create(self, validated_data):
        subtasks_data = validated_data.pop('subtasks', [])
        assigned_to_data = validated_data.pop('assigned_to', [])
        task = Task.objects.create(**validated_data)

        if assigned_to_data:
            task.assigned_to.set(assigned_to_data)

        for subtask_item in subtasks_data:
            subtask_item.pop('id', None)
            subtask_item.pop('task', None)
            Subtask.objects.create(task=task, **subtask_item)

        return task

    def update(self, instance, validated_data):
        subtasks_data = validated_data.pop('subtasks', None)
        assigned_to_data = validated_data.pop('assigned_to', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if assigned_to_data is not None:
            instance.assigned_to.set(assigned_to_data)

        if subtasks_data is not None:
            for subtask_item in subtasks_data:
                subtask_id = subtask_item.pop('id', None)
                subtask_item.pop('task', None)
                if subtask_id:
                    Subtask.objects.filter(id=subtask_id, task=instance).update(**subtask_item)
                else:
                    Subtask.objects.create(task=instance, **subtask_item)

        return instance


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    """
    author = serializers.CharField(source='author.fullname', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'task', 'author', 'created_at']


class BoardTaskSerializer(TaskSerializer):
    """
    Serializer for tasks with frontend-compatible status and priority representations.
    """
    def to_representation(self, instance):
        status_map = {
            'to_do': 'to-do',
            'in_progress': 'in-progress',
            'await_feedback': 'review',
        }
        prio_map = {
            'urgent': 'high',
        }
        data = super().to_representation(instance)
        if data.get('status') in status_map:
            data['status'] = status_map[data['status']]
        if data.get('priority') in prio_map:
            data['priority'] = prio_map[data['priority']]
        return data


class BoardUserSerializer(serializers.ModelSerializer):
    """
    Serializer für Benutzerdaten in Board-Darstellungen.
    """
    fullname = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class BoardSerializer(serializers.ModelSerializer):
    """
    Serializer für Boards mit Mitgliedern und Eigentümer.
    """
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )
    members_data = BoardUserSerializer(source='members', many=True, read_only=True)
    owner_data = BoardUserSerializer(source='owner', read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'members', 'members_data', 'owner_data']
        read_only_fields = ['id', 'members_data', 'owner_data']

    def to_internal_value(self, data):
        data_copy = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'members' in data_copy and isinstance(data_copy['members'], list):
            normalized = []
            for item in data_copy['members']:
                if isinstance(item, dict) and 'id' in item:
                    normalized.append(item['id'])
                else:
                    normalized.append(item)
            data_copy['members'] = normalized
        return super().to_internal_value(data_copy)


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password validation and optional full name.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    repeated_password = serializers.CharField(write_only=True, required=True)
    fullname = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'repeated_password',
            'first_name', 'last_name', 'fullname', 'color'
        ]
        extra_kwargs = {
            'username': {'required': False},
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'color': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        if not attrs.get('username') and attrs.get('email'):
            base_username = attrs['email'].split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            attrs['username'] = username

        fullname = attrs.get('fullname')
        if fullname and not attrs.get('first_name'):
            parts = fullname.strip().split(' ', 1)
            attrs['first_name'] = parts[0]
            attrs['last_name'] = parts[1] if len(parts) > 1 else ''

        return attrs

    def create(self, validated_data):
        validated_data.pop('repeated_password')
        validated_data.pop('fullname', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            color=validated_data.get('color', '#FF7A00')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login via username or email.
    """
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        username = attrs.get('username', '').strip() if attrs.get('username') else None
        email = attrs.get('email', '').strip() if attrs.get('email') else None
        password = attrs.get('password')

        if not username and not email:
            raise serializers.ValidationError("Please provide a username or an email address.")

        if email and not username:
            try:
                user_obj = User.objects.get(email__iexact=email)
                username = user_obj.username
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials.")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        attrs['user'] = user
        return attrs
