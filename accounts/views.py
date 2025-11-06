from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import UserProfile
from .serializers import UserProfileSerializer, UserSerializer

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """Get current user profile"""
    try:
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({
            'error': 'Profile not found. Please complete your profile.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST', 'PATCH'])
@permission_classes([IsAuthenticated])
def complete_profile(request):
    """Complete user profile after email verification"""
    if not request.user.is_email_verified:
        return Response({
            'error': 'Please verify your email first.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        request.user.profile_completed = True
        request.user.save()
        return Response({
            'message': 'Profile completed successfully',
            'profile': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return Response({
            'error': 'Profile not found. Please complete your profile first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'profile': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_profile_completion(request):
    """Check if user has completed profile"""
    user = request.user
    return Response({
        'email_verified': user.is_email_verified,
        'profile_completed': user.profile_completed,
        'can_submit': user.is_email_verified and user.profile_completed,
        'next_step': 'complete_profile' if user.is_email_verified and not user.profile_completed else 'verify_email' if not user.is_email_verified else 'ready'
    }, status=status.HTTP_200_OK)
