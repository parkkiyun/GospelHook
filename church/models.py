from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import pytz


class Church(models.Model):
    """교회 정보 모델"""
    
    # 기본 정보
    name = models.CharField(max_length=100, verbose_name='교회 이름')
    code = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True,
        verbose_name='교회 코드',
        validators=[RegexValidator(regex='^[A-Z0-9]+$', message='대문자와 숫자만 사용 가능합니다.')]
    )
    
    # 연락처 정보
    address = models.TextField(blank=True, verbose_name='주소')
    postal_code = models.CharField(max_length=10, blank=True, verbose_name='우편번호')
    phone = models.CharField(max_length=20, blank=True, verbose_name='대표 전화번호')
    email = models.EmailField(blank=True, verbose_name='대표 이메일')
    website = models.URLField(blank=True, verbose_name='홈페이지')
    
    # 담임목사 정보
    pastor_name = models.CharField(max_length=50, blank=True, verbose_name='담임목사')
    pastor_phone = models.CharField(max_length=20, blank=True, verbose_name='담임목사 연락처')
    
    # 교회 설정
    timezone = models.CharField(
        max_length=50, 
        default='Asia/Seoul', 
        verbose_name='시간대',
        choices=[(tz, tz) for tz in pytz.common_timezones]
    )
    founding_date = models.DateField(null=True, blank=True, verbose_name='창립일')
    
    # 교단 정보
    denomination = models.CharField(max_length=100, blank=True, verbose_name='교단')
    denomination_region = models.CharField(max_length=50, blank=True, verbose_name='교단 지역')
    registration_number = models.CharField(max_length=50, blank=True, verbose_name='교회 등록번호')
    
    # 시스템 설정
    domain = models.CharField(
        max_length=255, 
        unique=True, 
        null=True, 
        blank=True, 
        verbose_name='교회 도메인',
        help_text='예: mychurch.gospelhook.com'
    )
    is_active = models.BooleanField(default=True, verbose_name='활성화 상태')
    max_members = models.IntegerField(default=1000, verbose_name='최대 교인 수')
    
    # 커스텀 설정 (JSON)
    settings = models.JSONField(
        default=dict, 
        verbose_name='교회별 커스텀 설정',
        help_text='예배 시간, 부서 구조 등 교회별 설정'
    )
    
    # 파일 업로드
    logo = models.ImageField(upload_to='church/logos/', null=True, blank=True, verbose_name='교회 로고')
    
    # 공식 문서 이미지들
    church_seal = models.ImageField(
        upload_to='church/seals/', 
        null=True, 
        blank=True, 
        verbose_name='교회 직인',
        help_text='공식 문서에 사용되는 교회 직인 이미지'
    )
    membership_certificate_header = models.ImageField(
        upload_to='church/certificates/', 
        null=True, 
        blank=True, 
        verbose_name='교인증명서 헤더',
        help_text='교인증명서 상단에 들어갈 헤더 이미지 (교회명, 로고 등)'
    )
    baptism_certificate_header = models.ImageField(
        upload_to='church/certificates/', 
        null=True, 
        blank=True, 
        verbose_name='세례증명서 헤더', 
        help_text='세례증명서 상단에 들어갈 헤더 이미지'
    )
    affiliation_certificate_header = models.ImageField(
        upload_to='church/certificates/', 
        null=True, 
        blank=True, 
        verbose_name='소속증명서 헤더',
        help_text='소속증명서 상단에 들어갈 헤더 이미지'
    )
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'churches'
        verbose_name = '교회'
        verbose_name_plural = '교회들'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_worship_times(self):
        """예배 시간 정보 반환"""
        return self.settings.get('worship_times', {})
    
    def get_departments(self):
        """부서 구조 정보 반환"""
        return self.settings.get('departments', [])
    
    @property
    def member_count(self):
        """등록된 교인 수"""
        return self.members.filter(is_active=True).count()
    
    @property
    def is_full(self):
        """교인 수 제한 도달 여부"""
        return self.member_count >= self.max_members
    
    def get_timezone(self):
        """교회 시간대 객체 반환"""
        return pytz.timezone(self.timezone)
    
    def get_local_time(self):
        """교회 현지 시간 반환"""
        return timezone.now().astimezone(self.get_timezone())