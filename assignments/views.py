import os
import tempfile
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from django.core.files.storage import default_storage

from .file_extractors import FileExtractor
from .gemini_service import GeminiService
from .latex_converter import LaTeXConverter
from .utils import (
    generate_download_token, 
    get_expiry_time, 
    validate_file_type,
    format_error_response,
    format_success_response
)
from submissions.models import TemporaryDownload, DailySubmissionCount
from submissions.views import increment_submission_count


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def submit_assignment(request):
    """
    Main endpoint for assignment submission and processing
    Handles: validation -> extraction -> Gemini -> LaTeX -> PDF
    """
    user = request.user
    
    # Step 1: Check if profile is completed
    if not user.profile_completed:
        return Response(
            format_error_response(
                "Please complete your profile before submitting assignments",
                code='profile_incomplete'
            ),
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Step 2: Check daily submission limit
    today = timezone.now().date()
    daily_count, _ = DailySubmissionCount.objects.get_or_create(
        user=user,
        submission_date=today,
        defaults={'count': 0}
    )
    
    if daily_count.count >= settings.MAX_DAILY_SUBMISSIONS:
        return Response(
            format_error_response(
                f"Daily limit reached ({settings.MAX_DAILY_SUBMISSIONS} assignments per day). Try again tomorrow.",
                code='limit_reached'
            ),
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Step 3: Get form data
    uploaded_file = request.FILES.get('file')
    subject_name = request.data.get('subject_name', '').strip()
    assignment_number = request.data.get('assignment_number', '').strip()
    tutor_name = request.data.get('tutor_name', '').strip()
    
    # Validate required fields
    if not all([uploaded_file, subject_name, assignment_number, tutor_name]):
        return Response(
            format_error_response(
                "Missing required fields: file, subject_name, assignment_number, tutor_name",
                code='missing_fields'
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Step 4: Validate file type
    if not validate_file_type(uploaded_file.name):
        return Response(
            format_error_response(
                "Invalid file type. Only .pdf, .docx, and .pptx files are supported.",
                code='invalid_file_type'
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Step 5: Save uploaded file temporarily
    temp_file_path = None
    try:
        # Save file to temp location
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file.close()
        temp_file_path = temp_file.name
        
        # Step 6: Extract text from file
        try:
            extracted_text = FileExtractor.extract_text(temp_file_path)
        except Exception as e:
            return Response(
                format_error_response(
                    f"Failed to extract text from file: {str(e)}",
                    code='extraction_error'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 7: Check word count
        word_count = FileExtractor.count_words(extracted_text)
        if word_count > settings.MAX_WORD_COUNT:
            return Response(
                format_error_response(
                    f"Assignment exceeds {settings.MAX_WORD_COUNT} words (found {word_count} words). Please reduce content.",
                    code='word_limit_exceeded'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if word_count < 10:
            return Response(
                format_error_response(
                    "Extracted text is too short. Please ensure the file contains readable text.",
                    code='insufficient_content'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 8: Prepare metadata for Gemini
        metadata = {
            'subject_name': subject_name,
            'assignment_number': assignment_number,
            'tutor_name': tutor_name,
            'student_name': user.profile.full_name if hasattr(user, 'profile') else user.username,
            'registration_number': user.profile.registration_number if hasattr(user, 'profile') else 'N/A',
            'university_name': user.profile.university_name if hasattr(user, 'profile') else 'N/A',
            'department_name': user.profile.department_name if hasattr(user, 'profile') else 'N/A',
        }
        
        # Step 9: Generate LaTeX code using Gemini
        gemini_service = GeminiService()
        try:
            latex_code = gemini_service.generate_latex_solution(extracted_text, metadata)
        except Exception as e:
            return Response(
                format_error_response(
                    "Unable to generate solution. Please try again later.",
                    code='gemini_error'
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Step 10: Convert LaTeX to PDF (with retry logic)
        output_filename = LaTeXConverter.sanitize_filename(
            f"{metadata['student_name']}_{subject_name}_{assignment_number}.pdf"
        )
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            success, result = LaTeXConverter.latex_to_pdf(latex_code, output_filename)
            
            if success:
                pdf_path = result
                break
            else:
                error_message = result
                if attempt < max_retries:
                    # Retry with Gemini fix
                    try:
                        latex_code = gemini_service.retry_with_error(latex_code, error_message)
                    except:
                        pass  # Continue to next attempt or fail
                else:
                    # All retries failed
                    return Response(
                        format_error_response(
                            "Unable to generate solution. Please try again.",
                            code='latex_conversion_error'
                        ),
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        
        # Step 11: Create temporary download link
        token = generate_download_token()
        expires_at = get_expiry_time()
        
        temp_download = TemporaryDownload.objects.create(
            user=user,
            token=token,
            filename=output_filename,
            file_path=pdf_path,
            expires_at=expires_at
        )
        
        # Step 12: Increment submission counts
        increment_submission_count(user)
        
        # Step 13: Return success response
        download_url = f"/api/assignments/download/{token}/"
        
        return Response(
            format_success_response({
                'download_url': download_url,
                'filename': output_filename,
                'expires_in': settings.PDF_EXPIRY_MINUTES * 60,  # seconds
                'word_count': word_count,
                'submissions_remaining': settings.MAX_DAILY_SUBMISSIONS - (daily_count.count + 1)
            }, message='Assignment processed successfully'),
            status=status.HTTP_200_OK
        )
    
    finally:
        # Cleanup temporary uploaded file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@api_view(['GET'])
def download_assignment(request, token):
    """
    Download generated PDF using temporary token
    No authentication required (token-based access)
    """
    try:
        temp_download = TemporaryDownload.objects.get(token=token)
    except TemporaryDownload.DoesNotExist:
        raise Http404("Download link not found or expired")
    
    # Check if expired
    if temp_download.is_expired():
        # Delete expired record and file
        if os.path.exists(temp_download.file_path):
            os.remove(temp_download.file_path)
        temp_download.delete()
        raise Http404("Download link has expired")
    
    # Check if file exists
    if not os.path.exists(temp_download.file_path):
        temp_download.delete()
        raise Http404("File not found")
    
    # Mark as downloaded
    temp_download.downloaded = True
    temp_download.save()
    
    # Serve file
    response = FileResponse(
        open(temp_download.file_path, 'rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=temp_download.filename
    )
    
    return response
