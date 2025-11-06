from django.apps import AppConfig

class SubmissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'submissions'

    def ready(self):
        """Start scheduler when Django starts"""
        try:
            from submissions.scheduler import start_scheduler
            start_scheduler()
        except:
            pass
