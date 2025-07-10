from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid


class User(AbstractUser):
    """커스텀 사용자 모델"""
    email = models.EmailField(unique=True, verbose_name='이메일')
    is_verified = models.BooleanField(default=False, verbose_name='이메일 인증 여부')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'
    
    def __str__(self):
        return f"{self.username} ({self.email})"




class ChurchUser(models.Model):
    """교회별 사용자 정보"""
    ROLE_CHOICES = [
        ('super_admin', '슈퍼 관리자'),
        ('church_admin', '교회 관리자'),
        ('church_staff', '교회 직원'),
        ('member', '일반 교인'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='church_users', verbose_name='사용자')
    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, related_name='church_users', verbose_name='교회')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name='역할')
    name = models.CharField(max_length=50, verbose_name='이름')
    phone = models.CharField(max_length=20, blank=True, verbose_name='전화번호')
    notes = models.TextField(blank=True, verbose_name='메모')
    
    # 상태 관리
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='가입일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'church_users'
        verbose_name = '교회 사용자'
        verbose_name_plural = '교회 사용자들'
        unique_together = ['user', 'church']
        indexes = [
            models.Index(fields=['church', 'role']),
            models.Index(fields=['church', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.church.name})"
    
    @property
    def is_admin(self):
        """관리자 권한 여부"""
        return self.role in ['super_admin', 'church_admin']
    
    @property
    def is_staff(self):
        """직원 권한 여부"""
        return self.role in ['super_admin', 'church_admin', 'church_staff']