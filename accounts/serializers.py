from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import ActivationSerializer as BaseActivationSerializer
from .models import UserProfile

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """Custom user creation serializer - NOT inheriting from Djoser"""
    
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('id', 'email', 'password')
        extra_kwargs = {
            'email': {'required': True},
            'password': {'write_only': True}
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value.lower()
    
    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')
        
        username_base = email.split('@')[0].replace('.', '').replace('-', '').replace('_', '').replace('+', '')
        username = username_base.lower()
        
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.is_active = False
        user.save()
        
        return user


class ActivationSerializer(BaseActivationSerializer):
    def validate(self, attrs):
        result = super().validate(attrs)
        self.user.is_email_verified = True
        self.user.save()
        return result


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('full_name', 'university_name', 'registration_number', 'department_name')


class UserSerializer(serializers.ModelSerializer):
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
