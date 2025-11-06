from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create profile when user registers"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def sync_email_verified(sender, instance, **kwargs):
    """Sync is_active to is_email_verified when user is activated"""
    if instance.is_active and not instance.is_email_verified:
        instance.is_email_verified = True
        instance.save(update_fields=['is_email_verified'])
