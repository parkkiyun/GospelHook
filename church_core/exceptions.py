"""
GospelHook 프로젝트의 통일된 예외 처리 시스템
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.http import Http404
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
import logging
import traceback

logger = logging.getLogger(__name__)


class GospelHookException(Exception):
    """GospelHook 기본 예외 클래스"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "잘못된 요청입니다."
    default_code = "invalid_request"

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        
        self.detail = detail
        self.code = code
        super().__init__(detail)


class ChurchNotFoundError(GospelHookException):
    """교회를 찾을 수 없는 경우"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "교회를 찾을 수 없습니다."
    default_code = "church_not_found"


class MemberNotFoundError(GospelHookException):
    """교인을 찾을 수 없는 경우"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "교인을 찾을 수 없습니다."
    default_code = "member_not_found"


class PermissionDeniedError(GospelHookException):
    """권한이 없는 경우"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "해당 작업을 수행할 권한이 없습니다."
    default_code = "permission_denied"


class ValidationFailedError(GospelHookException):
    """유효성 검사 실패"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "입력 데이터가 유효하지 않습니다."
    default_code = "validation_failed"


class DuplicateDataError(GospelHookException):
    """중복 데이터 오류"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = "이미 존재하는 데이터입니다."
    default_code = "duplicate_data"


class BusinessLogicError(GospelHookException):
    """비즈니스 로직 오류"""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "비즈니스 규칙을 위반했습니다."
    default_code = "business_logic_error"


class FileUploadError(GospelHookException):
    """파일 업로드 오류"""
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "파일 업로드에 실패했습니다."
    default_code = "file_upload_error"


class ExternalServiceError(GospelHookException):
    """외부 서비스 오류"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "외부 서비스에 일시적인 문제가 발생했습니다."
    default_code = "external_service_error"


def custom_exception_handler(exc, context):
    """
    커스텀 예외 처리 핸들러
    모든 예외를 일관된 형식으로 응답
    """
    
    # DRF 기본 예외 처리기 호출
    response = exception_handler(exc, context)
    
    # 로깅을 위한 요청 정보 수집
    request = context.get('request')
    view = context.get('view')
    
    request_info = {
        'method': request.method if request else 'Unknown',
        'path': request.path if request else 'Unknown',
        'user': str(request.user) if request and hasattr(request, 'user') else 'Anonymous',
        'view': view.__class__.__name__ if view else 'Unknown'
    }
    
    # GospelHook 커스텀 예외 처리
    if isinstance(exc, GospelHookException):
        custom_response_data = {
            'error': {
                'code': exc.code,
                'message': str(exc.detail),
                'status_code': exc.status_code
            },
            'success': False,
            'timestamp': _get_timestamp()
        }
        
        logger.warning(
            f"GospelHook Exception: {exc.__class__.__name__} - {exc.detail}",
            extra={'request_info': request_info}
        )
        
        return Response(custom_response_data, status=exc.status_code)
    
    # Django 기본 예외들을 GospelHook 형식으로 변환
    if isinstance(exc, Http404):
        custom_response_data = {
            'error': {
                'code': 'not_found',
                'message': '요청한 리소스를 찾을 수 없습니다.',
                'status_code': status.HTTP_404_NOT_FOUND
            },
            'success': False,
            'timestamp': _get_timestamp()
        }
        
        logger.info(
            f"404 Not Found: {str(exc)}",
            extra={'request_info': request_info}
        )
        
        return Response(custom_response_data, status=status.HTTP_404_NOT_FOUND)
    
    if isinstance(exc, PermissionDenied):
        custom_response_data = {
            'error': {
                'code': 'permission_denied',
                'message': '해당 작업을 수행할 권한이 없습니다.',
                'status_code': status.HTTP_403_FORBIDDEN
            },
            'success': False,
            'timestamp': _get_timestamp()
        }
        
        logger.warning(
            f"Permission Denied: {str(exc)}",
            extra={'request_info': request_info}
        )
        
        return Response(custom_response_data, status=status.HTTP_403_FORBIDDEN)
    
    if isinstance(exc, ValidationError):
        custom_response_data = {
            'error': {
                'code': 'validation_error',
                'message': '입력 데이터가 유효하지 않습니다.',
                'details': str(exc),
                'status_code': status.HTTP_400_BAD_REQUEST
            },
            'success': False,
            'timestamp': _get_timestamp()
        }
        
        logger.info(
            f"Validation Error: {str(exc)}",
            extra={'request_info': request_info}
        )
        
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    if isinstance(exc, IntegrityError):
        custom_response_data = {
            'error': {
                'code': 'integrity_error',
                'message': '데이터 무결성 오류가 발생했습니다.',
                'status_code': status.HTTP_409_CONFLICT
            },
            'success': False,
            'timestamp': _get_timestamp()
        }
        
        logger.error(
            f"Integrity Error: {str(exc)}",
            extra={'request_info': request_info}
        )
        
        return Response(custom_response_data, status=status.HTTP_409_CONFLICT)
    
    # DRF 예외가 처리된 경우
    if response is not None:
        custom_response_data = {
            'error': {
                'code': 'api_error',
                'message': _extract_error_message(response.data),
                'details': response.data if isinstance(response.data, dict) else None,
                'status_code': response.status_code
            },
            'success': False,
            'timestamp': _get_timestamp()
        }
        
        logger.warning(
            f"DRF Exception: {exc.__class__.__name__} - {str(exc)}",
            extra={'request_info': request_info}
        )
        
        response.data = custom_response_data
        return response
    
    # 처리되지 않은 예외 (500 Internal Server Error)
    custom_response_data = {
        'error': {
            'code': 'internal_server_error',
            'message': '서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
        },
        'success': False,
        'timestamp': _get_timestamp()
    }
    
    # 심각한 오류는 상세 로깅
    logger.error(
        f"Unhandled Exception: {exc.__class__.__name__} - {str(exc)}",
        extra={
            'request_info': request_info,
            'traceback': traceback.format_exc()
        }
    )
    
    return Response(custom_response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_timestamp():
    """현재 시간을 ISO 형식으로 반환"""
    from datetime import datetime
    return datetime.now().isoformat()


def _extract_error_message(data):
    """DRF 에러 데이터에서 메시지 추출"""
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        elif 'non_field_errors' in data:
            return ', '.join(data['non_field_errors'])
        else:
            # 첫 번째 에러 메시지 반환
            for key, value in data.items():
                if isinstance(value, list) and value:
                    return f"{key}: {value[0]}"
                else:
                    return f"{key}: {value}"
    elif isinstance(data, list) and data:
        return str(data[0])
    else:
        return str(data)


# 편의 함수들
def raise_church_not_found(church_id=None):
    """교회를 찾을 수 없는 경우 예외 발생"""
    detail = f"교회 ID {church_id}를 찾을 수 없습니다." if church_id else "교회를 찾을 수 없습니다."
    raise ChurchNotFoundError(detail)


def raise_member_not_found(member_id=None):
    """교인을 찾을 수 없는 경우 예외 발생"""
    detail = f"교인 ID {member_id}를 찾을 수 없습니다." if member_id else "교인을 찾을 수 없습니다."
    raise MemberNotFoundError(detail)


def raise_permission_denied(action=None):
    """권한이 없는 경우 예외 발생"""
    detail = f"{action} 권한이 없습니다." if action else "해당 작업을 수행할 권한이 없습니다."
    raise PermissionDeniedError(detail)


def raise_validation_failed(message):
    """유효성 검사 실패 예외 발생"""
    raise ValidationFailedError(message)


def raise_duplicate_data(resource=None):
    """중복 데이터 예외 발생"""
    detail = f"이미 존재하는 {resource}입니다." if resource else "이미 존재하는 데이터입니다."
    raise DuplicateDataError(detail)


def raise_business_logic_error(message):
    """비즈니스 로직 오류 예외 발생"""
    raise BusinessLogicError(message)
