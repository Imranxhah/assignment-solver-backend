import os
from django.utils import timezone
from submissions.models import TemporaryDownload


def cleanup_expired_files():
    """
    Cleanup expired download files
    This task should be scheduled to run periodically via Django-Q
    """
    now = timezone.now()
    expired_downloads = TemporaryDownload.objects.filter(expires_at__lt=now)
    
    deleted_count = 0
    for download in expired_downloads:
        # Delete file if exists
        if os.path.exists(download.file_path):
            try:
                os.remove(download.file_path)
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting file {download.file_path}: {e}")
        
        # Delete database record
        download.delete()
    
    return f"Cleaned up {deleted_count} expired files"
