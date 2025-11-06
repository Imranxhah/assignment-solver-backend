from django.contrib.auth.models import AbstractUser
from django.db import models

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
