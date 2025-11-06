from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import ActivationSerializer as BaseActivationSerializer
from .models import UserProfile

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    """Custom user creation serializer"""
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'password')


class ActivationSerializer(BaseActivationSerializer):
    """Custom activation serializer - syncs is_email_verified"""
    def validate(self, attrs):
        # Call parent validation
        result = super().validate(attrs)
        # Mark email as verified when activated
        self.user.is_email_verified = True
        return result


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    class Meta:
        model = UserProfile
        fields = ('full_name', 'university_name', 'registration_number', 'department_name')


class UserSerializer(serializers.ModelSerializer):
    """User serializer with profile"""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'is_email_verified', 'profile_completed', 'profile')

class SendVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.is_active:
                raise serializers.ValidationError('User already verified')
        except User.DoesNotExist:
            raise serializers.ValidationError('User not found')
        return value

class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)