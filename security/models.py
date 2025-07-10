from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserSecurityProfile(models.Model):
    """사용자 보안 프로필 (별도 테이블)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_profile', verbose_name='사용자')
    failed_login_attempts = models.PositiveIntegerField(default=0, verbose_name='로그인 실패 횟수')
    locked_until = models.DateTimeField(null=True, blank=True, verbose_name='계정 잠금 해제 시간')
    last_failed_login = models.DateTimeField(null=True, blank=True, verbose_name='마지막 로그인 실패 시간')
    password_changed_at = models.DateTimeField(default=timezone.now, verbose_name='비밀번호 변경일')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='마지막 로그인 IP')
    
    class Meta:
        db_table = 'user_security_profiles'
        verbose_name = '사용자 보안 프로필'
        verbose_name_plural = '사용자 보안 프로필들'
    
    def __str__(self):
        return f"{self.user.username} 보안 프로필"
    
    @property
    def is_locked(self):
        """계정 잠금 여부 확인"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False
    
    def lock_account(self, duration_minutes=30):
        """계정 잠금"""
        self.locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['locked_until'])
    
    def unlock_account(self):
        """계정 잠금 해제"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_failed_login = None
        self.save(update_fields=['failed_login_attempts', 'locked_until', 'last_failed_login'])
    
    def record_failed_login(self, ip_address=None):
        """로그인 실패 기록"""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        if ip_address:
            self.last_login_ip = ip_address
        
        # 5회 실패 시 30분 잠금
        if self.failed_login_attempts >= 5:
            self.lock_account(30)
        
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'last_login_ip'])
    
    def record_successful_login(self, ip_address=None):
        """로그인 성공 기록"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        if ip_address:
            self.last_login_ip = ip_address
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'last_login_ip'])
    
    @property
    def password_expired(self):
        """비밀번호 만료 여부 (90일)"""
        return timezone.now() > self.password_changed_at + timedelta(days=90)


class JWTBlacklist(models.Model):
    """JWT 토큰 블랙리스트"""
    token_jti = models.CharField(max_length=255, unique=True, verbose_name='JWT ID')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='사용자')
    blacklisted_at = models.DateTimeField(default=timezone.now, verbose_name='블랙리스트 등록일')
    reason = models.CharField(max_length=100, verbose_name='블랙리스트 사유', choices=[
        ('logout', '로그아웃'),
        ('security', '보안상 이유'),
        ('expired', '만료'),
        ('revoked', '관리자 취소'),
    ])
    expires_at = models.DateTimeField(verbose_name='토큰 만료일')
    
    class Meta:
        db_table = 'jwt_blacklist'
        verbose_name = 'JWT 블랙리스트'
        verbose_name_plural = 'JWT 블랙리스트들'
        indexes = [
            models.Index(fields=['token_jti']),
            models.Index(fields=['user', 'blacklisted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.token_jti[:8]}..."
    
    @classmethod
    def is_blacklisted(cls, jti):
        """토큰이 블랙리스트에 있는지 확인"""
        return cls.objects.filter(token_jti=jti, expires_at__gt=timezone.now()).exists()
    
    @classmethod
    def cleanup_expired(cls):
        """만료된 블랙리스트 항목 정리"""
        return cls.objects.filter(expires_at__lte=timezone.now()).delete()


class ActivityLog(models.Model):
    """사용자 활동 로그"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs', verbose_name='사용자')
    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, null=True, blank=True, verbose_name='교회')
    action = models.CharField(max_length=100, verbose_name='액션')
    resource = models.CharField(max_length=100, verbose_name='리소스')
    resource_id = models.CharField(max_length=50, blank=True, verbose_name='리소스 ID')
    ip_address = models.GenericIPAddressField(verbose_name='IP 주소')
    user_agent = models.TextField(verbose_name='User Agent')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='생성일')
    
    class Meta:
        db_table = 'activity_logs'
        verbose_name = '활동 로그'
        verbose_name_plural = '활동 로그들'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['church', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"