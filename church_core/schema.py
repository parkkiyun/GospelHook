"""
GospelHook API 스키마 커스터마이징
drf-spectacular 스키마 생성 훅
"""
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


def custom_preprocessing_hook(endpoints):
    """
    API 엔드포인트 전처리 훅
    스키마 생성 전에 엔드포인트 정보를 수정
    """
    # 엔드포인트별 태그 자동 할당
    tag_mapping = {
        '/api/auth/': 'Authentication',
        '/api/v1/churches/': 'Churches',
        '/api/v1/users/': 'Users',
        '/api/v1/churches/{church_id}/members/': 'Members',
        '/api/v1/churches/{church_id}/groups/': 'Groups',
        '/api/v1/churches/{church_id}/attendance/': 'Attendance',
        '/api/v1/churches/{church_id}/prayers/': 'Prayers',
        '/api/v1/churches/{church_id}/carelog/': 'CareLog',
        '/api/v1/churches/{church_id}/bulletins/': 'Bulletins',
        '/api/v1/churches/{church_id}/worship/': 'Worship',
        '/api/v1/churches/{church_id}/announcements/': 'Announcements',
        '/api/v1/churches/{church_id}/education/': 'Education',
        '/api/v1/churches/{church_id}/offerings/': 'Offerings',
        '/api/v1/churches/{church_id}/volunteering/': 'Volunteering',
        '/api/v1/churches/{church_id}/surveys/': 'Surveys',
        '/api/v1/churches/{church_id}/bible/': 'Bible',
        '/api/v1/churches/{church_id}/reports/': 'Reports',
    }
    
    filtered_endpoints = []
    for (path, path_regex, method, callback) in endpoints:
        # 태그 자동 할당
        for prefix, tag in tag_mapping.items():
            if path.startswith(prefix):
                if hasattr(callback.cls, 'tags') and callback.cls.tags:
                    break  # 이미 태그가 설정된 경우
                callback.cls.tags = [tag]
                break
        
        # 내부 API나 디버그 엔드포인트 제외
        if any(exclude in path for exclude in ['/admin/', '/debug/', '/__debug__/']):
            continue
            
        filtered_endpoints.append((path, path_regex, method, callback))
    
    return filtered_endpoints


def custom_postprocessing_hook(result, generator, request, public):
    """
    스키마 생성 후처리 훅
    최종 스키마에 추가 정보 및 수정사항 적용
    """
    # API 정보 개선
    result['info']['contact'] = {
        'name': 'GospelHook 개발팀',
        'email': 'support@gospelhook.com',
        'url': 'https://gospelhook.com'
    }
    
    result['info']['license'] = {
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/MIT'
    }
    
    # 서버 정보 추가
    result['servers'] = [
        {
            'url': 'http://localhost:8000',
            'description': '개발 서버'
        },
        {
            'url': 'https://api.gospelhook.com',
            'description': '프로덕션 서버'
        }
    ]
    
    # 전역 보안 스키마 추가
    if 'components' not in result:
        result['components'] = {}
    
    if 'securitySchemes' not in result['components']:
        result['components']['securitySchemes'] = {}
    
    result['components']['securitySchemes']['jwtAuth'] = {
        'type': 'http',
        'scheme': 'bearer',
        'bearerFormat': 'JWT',
        'description': 'JWT 토큰을 사용한 인증입니다. 로그인 후 받은 access_token을 "Bearer {token}" 형식으로 Authorization 헤더에 포함해주세요.'
    }
    
    # 공통 에러 응답 스키마 추가
    if 'schemas' not in result['components']:
        result['components']['schemas'] = {}
    
    result['components']['schemas']['ErrorResponse'] = {
        'type': 'object',
        'properties': {
            'error': {
                'type': 'object',
                'properties': {
                    'code': {
                        'type': 'string',
                        'description': '에러 코드'
                    },
                    'message': {
                        'type': 'string',
                        'description': '에러 메시지'
                    },
                    'status_code': {
                        'type': 'integer',
                        'description': 'HTTP 상태 코드'
                    },
                    'details': {
                        'type': 'object',
                        'description': '추가 에러 정보 (선택적)'
                    }
                },
                'required': ['code', 'message', 'status_code']
            },
            'success': {
                'type': 'boolean',
                'description': '성공 여부 (항상 false)',
                'default': False
            },
            'timestamp': {
                'type': 'string',
                'format': 'date-time',
                'description': '에러 발생 시간'
            }
        },
        'required': ['error', 'success', 'timestamp']
    }
    
    # 페이지네이션 응답 스키마 추가
    result['components']['schemas']['PaginatedResponse'] = {
        'type': 'object',
        'properties': {
            'count': {
                'type': 'integer',
                'description': '전체 데이터 수'
            },
            'next': {
                'type': 'string',
                'nullable': True,
                'description': '다음 페이지 URL'
            },
            'previous': {
                'type': 'string',
                'nullable': True,
                'description': '이전 페이지 URL'
            },
            'results': {
                'type': 'array',
                'items': {},
                'description': '현재 페이지 데이터'
            }
        },
        'required': ['count', 'results']
    }
    
    # 각 경로에 공통 에러 응답 추가
    for path, path_info in result.get('paths', {}).items():
        for method, operation in path_info.items():
            if method in ['get', 'post', 'put', 'patch', 'delete']:
                if 'responses' not in operation:
                    operation['responses'] = {}
                
                # 공통 에러 응답 추가
                operation['responses']['400'] = {
                    'description': '잘못된 요청',
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/ErrorResponse'}
                        }
                    }
                }
                
                operation['responses']['401'] = {
                    'description': '인증 실패',
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/ErrorResponse'}
                        }
                    }
                }
                
                operation['responses']['403'] = {
                    'description': '권한 없음',
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/ErrorResponse'}
                        }
                    }
                }
                
                operation['responses']['404'] = {
                    'description': '리소스를 찾을 수 없음',
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/ErrorResponse'}
                        }
                    }
                }
                
                operation['responses']['500'] = {
                    'description': '서버 내부 오류',
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/ErrorResponse'}
                        }
                    }
                }
    
    # API 사용 예제 추가
    add_api_examples(result)
    
    return result


def add_api_examples(result):
    """
    API 사용 예제 추가
    """
    examples = {
        # 인증 예제
        '/api/auth/login/': {
            'post': {
                'requestBody': {
                    'content': {
                        'application/json': {
                            'example': {
                                'email': 'admin@example.com',
                                'password': 'password123'
                            }
                        }
                    }
                }
            }
        },
        
        # 교인 생성 예제
        '/api/v1/churches/{church_id}/members/': {
            'post': {
                'requestBody': {
                    'content': {
                        'application/json': {
                            'example': {
                                'name': '홍길동',
                                'gender': 'M',
                                'birth_date': '1990-01-01',
                                'phone': '010-1234-5678',
                                'email': 'hong@example.com',
                                'address': '서울시 강남구 역삼동',
                                'position': 'MEMBER'
                            }
                        }
                    }
                }
            }
        }
    }
    
    # 예제를 스키마에 적용
    for path, methods in examples.items():
        if path in result.get('paths', {}):
            for method, example_data in methods.items():
                if method in result['paths'][path]:
                    operation = result['paths'][path][method]
                    if 'requestBody' in example_data:
                        if 'requestBody' not in operation:
                            operation['requestBody'] = {}
                        if 'content' not in operation['requestBody']:
                            operation['requestBody']['content'] = {}
                        
                        for content_type, content_data in example_data['requestBody']['content'].items():
                            if content_type not in operation['requestBody']['content']:
                                operation['requestBody']['content'][content_type] = {}
                            operation['requestBody']['content'][content_type].update(content_data)


class CustomAutoSchema(AutoSchema):
    """
    커스텀 스키마 생성기
    더 상세한 API 문서를 위한 확장
    """
    
    def get_operation_id(self):
        """
        Operation ID 생성 규칙 커스터마이징
        """
        operation_id = super().get_operation_id()
        
        # 더 읽기 쉬운 operation ID 생성
        if hasattr(self.view, 'action'):
            action = self.view.action
            model_name = getattr(self.view, 'queryset', None)
            if model_name:
                model_name = model_name.model._meta.object_name
                return f"{action}_{model_name}"
        
        return operation_id
    
    def get_description(self):
        """
        API 설명 자동 생성
        """
        description = super().get_description()
        
        if not description and hasattr(self.view, '__doc__'):
            description = self.view.__doc__
        
        # 기본 설명 추가
        if not description:
            if hasattr(self.view, 'action'):
                action_descriptions = {
                    'list': '목록을 조회합니다.',
                    'create': '새로운 항목을 생성합니다.',
                    'retrieve': '특정 항목의 상세 정보를 조회합니다.',
                    'update': '특정 항목을 수정합니다.',
                    'partial_update': '특정 항목을 부분 수정합니다.',
                    'destroy': '특정 항목을 삭제합니다.',
                }
                description = action_descriptions.get(self.view.action, '작업을 수행합니다.')
        
        return description
    
    def get_tags(self):
        """
        태그 자동 생성
        """
        tags = super().get_tags()
        
        if not tags and hasattr(self.view, 'queryset'):
            model_name = self.view.queryset.model._meta.verbose_name_plural
            tags = [model_name.title()]
        
        return tags