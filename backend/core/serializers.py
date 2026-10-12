from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from .models import Contact, Task, Subtask

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 'color']


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'phone', 'color', 'created_at']
        read_only_fields = ['id', 'created_at']


class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ['id', 'task', 'title', 'is_completed', 'created_at']
        read_only_fields = ['id', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_details = ContactSerializer(source='assigned_to', many=True, read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(many=True, queryset=Contact.objects.all(), required=False)
    subtasks = SubtaskSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'due_date', 'priority',
            'status', 'category', 'assigned_to', 'assigned_to_details',
            'subtasks', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']



class RegistrationSerializer(serializers.ModelSerializer):
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
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
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
