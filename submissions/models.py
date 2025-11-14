from django.db import models
from django.conf import settings
from django.utils import timezone

class DailySubmissionCount(models.Model):
    """Track daily submission count per user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_submissions')
    submission_date = models.DateField(default=timezone.now)
    count = models.IntegerField(default=0)
    # ✅ NEW: Track extra submissions from ads
    bonus_submissions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'submission_date')
        ordering = ['-submission_date']

    def __str__(self):
        return f"{self.user.email} - {self.submission_date} - {self.count} submissions"
    
    # ✅ NEW: Get effective max limit including bonuses
    def get_max_limit(self):
        return settings.MAX_DAILY_SUBMISSIONS + self.bonus_submissions

class TotalSubmissionCount(models.Model):
    """Track total submission count per user"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='total_submissions')
    total_count = models.IntegerField(default=0)
    last_submission_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Total: {self.total_count}"

class TemporaryDownload(models.Model):
    """Track temporary download links"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    downloaded = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.filename} - {self.token[:8]}..."
