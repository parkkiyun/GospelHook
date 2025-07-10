from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import time
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """API Rate Limiting Middleware"""
    
    def process_request(self, request):
        # API 경로에만 적용
        if not request.path.startswith('/api/'):
            return None
            
        # 인증된 사용자와 익명 사용자 구분
        if request.user.is_authenticated:
            identifier = f"user_{request.user.id}"
            # 인증된 사용자: 분당 100 요청
            max_requests = 100
            window = 60  # 초
        else:
            # IP 기반 제한
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            identifier = f"ip_{ip}"
            # 익명 사용자: 분당 20 요청
            max_requests = 20
            window = 60  # 초
        
        # 캐시 키
        cache_key = f"ratelimit_{identifier}"
        
        # 현재 요청 수 가져오기
        requests_data = cache.get(cache_key, {'count': 0, 'window_start': time.time()})
        
        # 시간 창 확인
        if time.time() - requests_data['window_start'] > window:
            # 새로운 시간 창 시작
            requests_data = {'count': 1, 'window_start': time.time()}
        else:
            requests_data['count'] += 1
        
        # 제한 확인
        if requests_data['count'] > max_requests:
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'최대 {max_requests}개 요청/{window}초를 초과했습니다.',
                'retry_after': int(window - (time.time() - requests_data['window_start']))
            }, status=429)
        
        # 캐시 업데이트
        cache.set(cache_key, requests_data, window)
        
        return None


class SecurityMiddleware(MiddlewareMixin):
    """보안 강화 미들웨어"""
    
    def process_response(self, request, response):
        # 보안 헤더 추가
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # API 응답에 추가 보안 헤더
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            
        return response


class ActivityLogMiddleware(MiddlewareMixin):
    """사용자 활동 로깅 미들웨어"""
    
    def process_request(self, request):
        request._start_time = time.time()
        
    def process_response(self, request, response):
        # API 요청만 로깅
        if request.path.startswith('/api/') and request.user.is_authenticated:
            duration = time.time() - getattr(request, '_start_time', time.time())
            self.log_activity(request, response, duration)
            
        return response

    def log_activity(self, request, response, duration):
        """활동 로그 저장"""
        try:
            from security.models import ActivityLog
            
            # Church ID 추출
            church_id = None
            if hasattr(request.user, 'church_users'):
                church_user = request.user.church_users.filter(is_active=True).first()
                if church_user:
                    church_id = church_user.church_id

            ActivityLog.objects.create(
                user=request.user,
                church_id=church_id,
                action=f"{request.method} {request.path}",
                resource=self.extract_resource(request.path),
                resource_id=self.extract_resource_id(request.path),
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
        except Exception as e:
            # 로깅 실패해도 요청은 계속 처리
            logger.error(f"Activity logging failed: {e}")

    def extract_resource(self, path):
        """경로에서 리소스 추출"""
        parts = path.strip('/').split('/')
        if len(parts) >= 3:
            return parts[2]  # /api/v1/members -> members
        return 'unknown'

    def extract_resource_id(self, path):
        """경로에서 리소스 ID 추출"""
        parts = path.strip('/').split('/')
        if len(parts) >= 4 and parts[3].isdigit():
            return parts[3]
        return ''

    def get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip