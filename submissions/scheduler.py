from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
import os
from submissions.models import TemporaryDownload

def cleanup_expired_files():
    """Delete PDFs older than 10 minutes"""
    now = timezone.now()
    expired = TemporaryDownload.objects.filter(expires_at__lt=now)
    
    count = 0
    for download in expired:
        if os.path.exists(download.file_path):
            try:
                os.remove(download.file_path)
                count += 1
            except:
                pass
        download.delete()
    
    print(f"✅ Cleaned {count} expired PDFs")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cleanup_expired_files,
        'interval',
        minutes=5,  # Check every 5 minutes
        id='cleanup_pdfs',
        replace_existing=True
    )
    if not scheduler.running:
        scheduler.start()
        print("🚀 Scheduler started!")

