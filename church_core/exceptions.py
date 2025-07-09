from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    # DRF의 기본 예외 핸들러를 호출하여 표준 응답을 얻습니다.
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'errors': []
        }

        # DRF의 기본 에러 응답 구조를 우리가 정의한 형식으로 변환합니다.
        # 예를 들어, validation 에러의 경우 details를 field_errors로 변환
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            field_errors = {}
            for field, errors in exc.detail.items():
                field_errors[field] = [str(error) for error in errors]
            custom_response_data['errors'].append({
                'status_code': response.status_code,
                'error_code': exc.__class__.__name__.upper().replace('EXCEPTION', '').replace('REST_FRAMEWORK', '').replace(' ', '_'),
                'message': '입력값이 올바르지 않습니다.',
                'field_errors': field_errors
            })
        else:
            custom_response_data['errors'].append({
                'status_code': response.status_code,
                'error_code': exc.__class__.__name__.upper().replace('EXCEPTION', '').replace('REST_FRAMEWORK', '').replace(' ', '_'),
                'message': getattr(exc, 'detail', '알 수 없는 오류가 발생했습니다.')
            })
        response.data = custom_response_data
    return response
