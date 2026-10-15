from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from .models import Contact, Task, Subtask

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer für die Profildaten des angemeldeten Benutzers.
    """
    user_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 'color']


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer für Kontakte mit automatischer Bereinigung von Leerzeichen.
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
    Serializer für Subtasks, nutzbar als Einzelendpunkt oder verschachtelt.
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
            raise serializers.ValidationError({"task": "Dieses Feld ist erforderlich."})
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer für Tasks inklusive verschachtelter Subtasks und Kontaktdetails.
    """
    assigned_to_details = ContactSerializer(source='assigned_to', many=True, read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(many=True, queryset=Contact.objects.all(), required=False)
    subtasks = SubtaskSerializer(many=True, required=False)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'due_date', 'priority',
            'status', 'category', 'assigned_to', 'assigned_to_details',
            'subtasks', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        data_copy = data.copy() if hasattr(data, 'copy') else dict(data)

        if 'assigned_to' in data_copy and data_copy['assigned_to'] is None:
            data_copy['assigned_to'] = []

        if 'due_date' in data_copy and data_copy['due_date'] == '':
            data_copy['due_date'] = None

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


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer für die Benutzerregistrierung mit Passwort-Validierung.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    repeated_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'first_name', 'last_name', 'color']
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'color': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError({"password": "Die Passwörter stimmen nicht überein."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('repeated_password')
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
    Serializer für den Benutzer-Login via Benutzername oder E-Mail.
    """
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        username = attrs.get('username', '').strip() if attrs.get('username') else None
        email = attrs.get('email', '').strip() if attrs.get('email') else None
        password = attrs.get('password')

        if not username and not email:
            raise serializers.ValidationError("Bitte gib einen Benutzernamen oder eine E-Mail-Adresse an.")

        if email and not username:
            try:
                user_obj = User.objects.get(email__iexact=email)
                username = user_obj.username
            except User.DoesNotExist:
                raise serializers.ValidationError("Ungültige Anmeldedaten.")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Ungültige Anmeldedaten.")
        if not user.is_active:
            raise serializers.ValidationError("Benutzerkonto ist deaktiviert.")

        attrs['user'] = user
        return attrs
