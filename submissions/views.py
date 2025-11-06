from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.conf import settings
from .models import DailySubmissionCount, TotalSubmissionCount


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_submission_limit(request):
    """Check if user can submit today"""
    user = request.user
    today = timezone.now().date()
    
    # Get or create daily count
    daily_count, _ = DailySubmissionCount.objects.get_or_create(
        user=user,
        submission_date=today,
        defaults={'count': 0}
    )
    
    # Check limit
    can_submit = daily_count.count < settings.MAX_DAILY_SUBMISSIONS
    remaining = max(0, settings.MAX_DAILY_SUBMISSIONS - daily_count.count)
    
    return Response({
        'can_submit': can_submit,
        'submissions_today': daily_count.count,
        'max_submissions': settings.MAX_DAILY_SUBMISSIONS,
        'remaining': remaining
    })


def increment_submission_count(user):
    """Helper function to increment submission counts"""
    today = timezone.now().date()
    
    # Update daily count
    daily_count, _ = DailySubmissionCount.objects.get_or_create(
        user=user,
        submission_date=today,
        defaults={'count': 0}
    )
    daily_count.count += 1
    daily_count.save()
    
    # Update total count
    total_count, _ = TotalSubmissionCount.objects.get_or_create(
        user=user,
        defaults={'total_count': 0}
    )
    total_count.total_count += 1
    total_count.last_submission_at = timezone.now()
    total_count.save()
    
    return daily_count.count, total_count.total_count
