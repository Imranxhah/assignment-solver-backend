import os
import secrets
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


def generate_download_token():
    """Generate secure random token for download"""
    return secrets.token_urlsafe(32)


def get_expiry_time():
    """Get expiry time for download (20 minutes from now)"""
    return timezone.now() + timedelta(minutes=settings.PDF_EXPIRY_MINUTES)


def validate_file_type(filename):
    """Validate if file type is supported"""
    allowed_extensions = ['.pdf', '.docx', '.pptx']
    _, extension = os.path.splitext(filename.lower())
    return extension in allowed_extensions


def format_error_response(message, code='error'):
    """Format error response"""
    return {
        'status': 'error',
        'code': code,
        'message': message
    }


def format_success_response(data, message='Success'):
    """Format success response"""
    return {
        'status': 'success',
        'message': message,
        'data': data
    }
