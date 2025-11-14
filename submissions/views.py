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
        defaults={'count': 0, 'bonus_submissions': 0}
    )
    
    # ✅ UPDATED: Calculate max with bonuses
    max_limit = daily_count.get_max_limit()
    can_submit = daily_count.count < max_limit
    remaining = max(0, max_limit - daily_count.count)
    
    return Response({
        'can_submit': can_submit,
        'submissions_today': daily_count.count,
        'max_submissions': settings.MAX_DAILY_SUBMISSIONS,  # Base limit (2)
        'bonus_submissions': daily_count.bonus_submissions,  # Extra from ads
        'total_max_submissions': max_limit,  # Total available (2 + bonuses)
        'remaining': remaining
    })

# ✅ NEW: Reward ad endpoint
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reward_ad_watched(request):
    """Increase daily submission limit when user watches rewarded ad"""
    user = request.user
    today = timezone.now().date()
    
    # Get or create daily count
    daily_count, _ = DailySubmissionCount.objects.get_or_create(
        user=user,
        submission_date=today,
        defaults={'count': 0, 'bonus_submissions': 0}
    )
    
    # ✅ Increase bonus by 1
    daily_count.bonus_submissions += 1
    daily_count.save()
    
    # Calculate new limits
    max_limit = daily_count.get_max_limit()
    remaining = max(0, max_limit - daily_count.count)
    
    return Response({
        'success': True,
        'message': 'Submission limit increased by 1',
        'bonus_submissions': daily_count.bonus_submissions,
        'total_max_submissions': max_limit,
        'remaining': remaining,
        'submissions_today': daily_count.count
    })

def increment_submission_count(user):
    """Helper function to increment submission counts"""
    today = timezone.now().date()
    
    # Update daily count
    daily_count, _ = DailySubmissionCount.objects.get_or_create(
        user=user,
        submission_date=today,
        defaults={'count': 0, 'bonus_submissions': 0}
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
