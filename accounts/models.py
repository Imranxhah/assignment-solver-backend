from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    """Custom user model with email as username"""
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """User profile with university details"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    university_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100)
    department_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.university_name}"


class VerificationCode(models.Model):
    """Store temporary OTP codes for email verification"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_code')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)
    attempts = models.IntegerField(default=0)
    
    def is_valid(self):
        return (timezone.now() - self.created_at) < timedelta(minutes=10)
    
    def is_attempts_exceeded(self):
        return self.attempts >= 5
    
    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))
    
    def __str__(self):
        return f'{self.user.email} - {self.code}'