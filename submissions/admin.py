from django.contrib import admin
from .models import DailySubmissionCount, TotalSubmissionCount, TemporaryDownload


@admin.register(DailySubmissionCount)
class DailySubmissionCountAdmin(admin.ModelAdmin):
    list_display = ('user', 'submission_date', 'count', 'created_at')
    list_filter = ('submission_date',)
    search_fields = ('user__email',)


@admin.register(TotalSubmissionCount)
class TotalSubmissionCountAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_count', 'last_submission_at', 'created_at')
    search_fields = ('user__email',)


@admin.register(TemporaryDownload)
class TemporaryDownloadAdmin(admin.ModelAdmin):
    list_display = ('user', 'filename', 'token', 'created_at', 'expires_at', 'downloaded')
    list_filter = ('downloaded', 'created_at')
    search_fields = ('user__email', 'filename')
