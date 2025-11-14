import os
import tempfile
import logging
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

# ✅ Setup logging
logger = logging.getLogger(__name__)

# ✅ Create temp directory in BASE_DIR (not /tmp/)
TEMP_DIR = os.path.join(settings.BASE_DIR, 'temp_uploads')
os.makedirs(TEMP_DIR, exist_ok=True)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def submit_assignment(request):
    """
    Main endpoint for assignment submission and processing.
    Supports both FILE and TEXT submissions.
    """
    user = request.user

    # Step 1: Check if profile is completed
    if not user.profile_completed:
        return Response(
            format_error_response(
                'Please complete your profile before submitting assignments',
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
                f'Daily limit reached ({settings.MAX_DAILY_SUBMISSIONS} assignments per day). Try again tomorrow.',
                code='limit_reached'
            ),
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    submission_type = request.data.get('type', 'FILE').upper()
    subject_name = request.data.get('subject_name', '').strip()
    assignment_number = request.data.get('assignment_number', '').strip()
    tutor_name = request.data.get('tutor_name', '').strip()

    # Validate required fields
    if not all([subject_name, assignment_number, tutor_name]):
        return Response(
            format_error_response(
                'Missing required fields: subject_name, assignment_number, tutor_name',
                code='missing_fields'
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    extracted_text = None
    temp_file_path = None

    if submission_type == 'FILE':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                format_error_response(
                    'No file uploaded',
                    code='missing_file'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        if not validate_file_type(uploaded_file.name):
            return Response(
                format_error_response(
                    'Invalid file type. Only .pdf, .docx, and .pptx files are supported.',
                    code='invalid_file_type'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # ✅ FIXED - Use custom temp directory instead of /tmp/
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(uploaded_file.name)[1],
                dir=TEMP_DIR  # ✅ Use our writable directory
            )
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file.close()
            temp_file_path = temp_file.name
            
            logger.info(f"File saved to {temp_file_path}")
            extracted_text = FileExtractor.extract_text(temp_file_path)
            
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            return Response(
                format_error_response(
                    f'Failed to extract text from file: {str(e)}',
                    code='extraction_error'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

    elif submission_type == 'TEXT':
        text_content = request.data.get('text_content', '').strip()
        if not text_content:
            return Response(
                format_error_response(
                    'No text content provided',
                    code='missing_text'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        extracted_text = text_content
    else:
        return Response(
            format_error_response(
                'Invalid submission type. Must be FILE or TEXT',
                code='invalid_type'
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    word_count = FileExtractor.count_words(extracted_text)

    if word_count > settings.MAX_WORD_COUNT:
        return Response(
            format_error_response(
                f'Assignment exceeds {settings.MAX_WORD_COUNT} words (found {word_count} words). Please reduce content.',
                code='word_limit_exceeded'
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    if word_count < 3:
        return Response(
            format_error_response(
                'Extracted text is too short. Please ensure the content contains at least 3 words.',
                code='insufficient_content'
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    metadata = {
        'subject_name': subject_name,
        'assignment_number': assignment_number,
        'tutor_name': tutor_name,
        'student_name': user.profile.full_name if hasattr(user, 'profile') else user.username,
        'registration_number': user.profile.registration_number if hasattr(user, 'profile') else 'N/A',
        'university_name': user.profile.university_name if hasattr(user, 'profile') else 'N/A',
        'department_name': user.profile.department_name if hasattr(user, 'profile') else 'N/A',
    }

    try:
        gemini_service = GeminiService()

        try:
            logger.info("Starting Gemini processing...")
            latex_code = gemini_service.generate_latex_solution(extracted_text, metadata)
            logger.info("Gemini completed")
        except Exception as e:
            logger.error(f"Gemini error: {str(e)}")
            return Response(
                format_error_response(
                    'Unable to generate solution. Please try again later.',
                    code='gemini_error'
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        output_filename = LaTeXConverter.sanitize_filename(
            f"{metadata['student_name']}_{subject_name}_{assignment_number}.pdf"
        )

        max_retries = 2
        for attempt in range(max_retries + 1):
            logger.info(f"LaTeX attempt {attempt + 1}")
            success, result = LaTeXConverter.latex_to_pdf(latex_code, output_filename)
            if success:
                pdf_path = result
                logger.info("LaTeX conversion successful")
                break
            else:
                error_message = result
                logger.warning(f"LaTeX failed: {error_message}")
                if attempt < max_retries:
                    try:
                        latex_code = gemini_service.retry_with_error(latex_code, error_message)
                    except:
                        pass
        else:
            return Response(
                format_error_response(
                    'Unable to generate solution. Please try again.',
                    code='latex_conversion_error'
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        token = generate_download_token()
        expires_at = get_expiry_time()

        temp_download = TemporaryDownload.objects.create(
            user=user,
            token=token,
            filename=output_filename,
            file_path=pdf_path,
            expires_at=expires_at
        )

        increment_submission_count(user)

        download_url = f'/api/assignments/download/{token}/'
        logger.info(f"Success for user {user.username}")

        return Response(
            format_success_response({
                'download_url': download_url,
                'filename': output_filename,
                'expires_in': settings.PDF_EXPIRY_MINUTES * 60,
                'word_count': word_count,
                'submissions_remaining': settings.MAX_DAILY_SUBMISSIONS - (daily_count.count + 1),
            }, message='Assignment processed successfully'),
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return Response(
            format_error_response(
                'An unexpected error occurred. Please try again.',
                code='server_error'
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # ✅ Cleanup
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Cleanup failed: {str(e)}")


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

    if temp_download.is_expired():
        if os.path.exists(temp_download.file_path):
            os.remove(temp_download.file_path)
        temp_download.delete()
        raise Http404("Download link has expired")

    if not os.path.exists(temp_download.file_path):
        temp_download.delete()
        raise Http404("File not found")

    temp_download.downloaded = True
    temp_download.save()

    response = FileResponse(
        open(temp_download.file_path, 'rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=temp_download.filename
    )

    return response
