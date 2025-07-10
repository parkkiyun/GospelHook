from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from security.models import JWTBlacklist
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    """JWT 블랙리스트 기능이 추가된 커스텀 JWT 인증"""

    def get_validated_token(self, raw_token):
        """토큰 검증 시 블랙리스트 확인"""
        validated_token = super().get_validated_token(raw_token)
        
        # JTI 추출
        try:
            jti = validated_token.get('jti')
            if jti and JWTBlacklist.is_blacklisted(jti):
                raise InvalidToken('Token is blacklisted')
        except Exception as e:
            logger.warning(f"JWT blacklist check failed: {e}")
            # 블랙리스트 확인 실패 시에도 계속 진행 (가용성 우선)
            
        return validated_token

    def get_user(self, validated_token):
        """사용자 정보 조회 시 계정 잠금 확인"""
        user = super().get_user(validated_token)
        
        # 보안 프로필 확인
        try:
            security_profile = user.security_profile
            if security_profile.is_locked:
                raise InvalidToken('Account is locked')
                
            if security_profile.password_expired:
                logger.info(f"User {user.id} password expired")
                # 비밀번호 만료 시에도 로그인 허용하되 경고만 로깅
        except AttributeError:
            # 보안 프로필이 없는 경우 생성
            from security.models import UserSecurityProfile
            UserSecurityProfile.objects.get_or_create(user=user)
            
        return user


def blacklist_token(token, reason='logout'):
    """토큰을 블랙리스트에 추가"""
    try:
        from rest_framework_simplejwt.tokens import UntypedToken
        from django.utils import timezone
        
        # 토큰 파싱
        untyped_token = UntypedToken(token)
        jti = untyped_token.get('jti')
        user_id = untyped_token.get('user_id')
        exp = untyped_token.get('exp')
        
        # 만료일 계산
        expires_at = timezone.datetime.fromtimestamp(exp, tz=timezone.get_current_timezone())
        
        # 블랙리스트에 추가
        user = User.objects.get(id=user_id)
        JWTBlacklist.objects.get_or_create(
            token_jti=jti,
            defaults={
                'user': user,
                'reason': reason,
                'expires_at': expires_at
            }
        )
        
        logger.info(f"Token blacklisted for user {user_id}: {reason}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")
        return False


def cleanup_expired_blacklist():
    """만료된 블랙리스트 항목 정리"""
    try:
        deleted_count, _ = JWTBlacklist.cleanup_expired()
        logger.info(f"Cleaned up {deleted_count} expired blacklist entries")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to cleanup blacklist: {e}")
        return 0