from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import UserProfile
from .serializers import UserProfileSerializer, UserSerializer
from django.core.mail import send_mail
from django.conf import settings
from .models import VerificationCode
from .serializers import SendVerificationCodeSerializer, VerifyCodeSerializer
from .models import AppVersion

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

# ✅ FIX: Allow unauthenticated access for email verification
@api_view(['POST'])
@permission_classes([AllowAny])
def send_verification_code(request):
    """Send OTP code to user's email"""
    serializer = SendVerificationCodeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found. Please register first.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Generate code
    code_obj, created = VerificationCode.objects.get_or_create(user=user)
    code_obj.code = VerificationCode.generate_code()
    code_obj.attempts = 0
    code_obj.save()
    
    # Send email
    try:
        send_mail(
            subject='Assignment Solver - Your Verification Code',
            message=f'Your verification code is: {code_obj.code}\n\nValid for 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
            recipient_list=[email],
        )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(
        {'success': True, 'message': f'Code sent to {email}'},
        status=status.HTTP_200_OK
    )

# ✅ FIX: Allow unauthenticated access for email verification
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_code(request):
    """Verify OTP code and mark email verified"""
    serializer = VerifyCodeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    code = serializer.validated_data['code']
    
    try:
        user = User.objects.get(email=email)
        code_obj = VerificationCode.objects.get(user=user)
    except (User.DoesNotExist, VerificationCode.DoesNotExist):
        return Response(
            {'error': 'Invalid email'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check validity
    if not code_obj.is_valid():
        code_obj.delete()
        return Response(
            {'error': 'Code expired. Request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if code_obj.is_attempts_exceeded():
        return Response(
            {'error': 'Too many attempts. Request a new code.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    if code_obj.code != code:
        code_obj.attempts += 1
        code_obj.save()
        remaining = 5 - code_obj.attempts
        return Response(
            {'error': f'Invalid code. {remaining} attempts remaining.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    

    user.is_email_verified = True
    user.is_active = True
    user.save()
    code_obj.delete()
    
    return Response(
        {'success': True, 'message': 'Email verified successfully!'},
        status=status.HTTP_200_OK
    )

@api_view(['GET'])
@permission_classes([AllowAny])
def check_version(request):
    """Check if app needs forced update"""
    app_version = request.query_params.get('version')
    
    if not app_version:
        return Response({'error': 'version parameter required'}, status=400)
    
    try:
        config = AppVersion.objects.first()
        
        # If no config or force update disabled, allow all versions
        if not config or not config.force_update_enabled:
            return Response({'force_update': False})
        
        # Simple version comparison (assumes format: 1.0.0)
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        needs_update = version_tuple(app_version) < version_tuple(config.minimum_version)
        
        return Response({
            'force_update': needs_update,
            'minimum_version': config.minimum_version,
            'update_url': config.update_url if needs_update else None,
            'message': config.update_message if needs_update else None
        })
        
    except Exception as e:
        # On any error, don't block users
        return Response({'force_update': False})

# Add this at the end of views.py
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification(request):
    """Resend verification code for inactive accounts"""
    email = request.data.get('email')
    
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Check if account is inactive (not verified)
        if user.is_active:
            return Response(
                {'error': 'This account is already verified. Please login.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new code (reuse existing logic)
        code_obj, created = VerificationCode.objects.get_or_create(user=user)
        code_obj.code = VerificationCode.generate_code()
        code_obj.attempts = 0
        code_obj.save()
        
        # Send email
        send_mail(
            subject='Assignment Solver - Your Verification Code',
            message=f'Your verification code is: {code_obj.code}\n\nValid for 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@example.com',
            recipient_list=[email],
        )
        
        return Response({
            'success': True,
            'message': 'Verification code sent. Please check your email.',
            'is_new_account': False
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'No account found with this email. Please register first.'},
            status=status.HTTP_404_NOT_FOUND
        )
