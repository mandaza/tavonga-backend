from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'address',
            'emergency_contact', 'emergency_phone', 'date_of_birth'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    is_carer = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'address', 'emergency_contact', 'emergency_phone',
            'profile_image', 'date_of_birth', 'hire_date', 'is_active_carer',
            'is_admin', 'approved', 'is_carer', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'is_admin', 'approved', 'created_at', 'updated_at']


class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    is_carer = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'is_admin', 'approved', 'is_active_carer', 'is_carer',
            'created_at'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'address',
            'emergency_contact', 'emergency_phone', 'profile_image',
            'date_of_birth'
        ]


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    is_carer = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'address', 'emergency_contact', 'emergency_phone',
            'profile_image', 'date_of_birth', 'hire_date', 'is_active_carer',
            'is_admin', 'approved', 'is_carer', 'created_at', 'updated_at'
        ] 