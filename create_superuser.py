#!/usr/bin/env python
"""
슈퍼유저 생성 스크립트
"""
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_core.settings')
django.setup()

from django.contrib.auth import get_user_model
from security.models import UserSecurityProfile

User = get_user_model()

# 슈퍼유저 정보
SUPERUSER_DATA = {
    'username': 'admin',
    'email': 'admin@gospelhook.com',
    'password': 'GospelHook2025!',
    'is_superuser': True,
    'is_staff': True,
    'is_active': True
}

def create_superuser():
    """슈퍼유저 생성"""
    
    # 기존 슈퍼유저 확인
    if User.objects.filter(username=SUPERUSER_DATA['username']).exists():
        print(f"슈퍼유저 '{SUPERUSER_DATA['username']}'가 이미 존재합니다.")
        user = User.objects.get(username=SUPERUSER_DATA['username'])
    else:
        # 새 슈퍼유저 생성
        user = User.objects.create_user(
            username=SUPERUSER_DATA['username'],
            email=SUPERUSER_DATA['email'],
            password=SUPERUSER_DATA['password']
        )
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        print(f"슈퍼유저 '{SUPERUSER_DATA['username']}'를 생성했습니다.")
    
    # 보안 프로필 생성
    security_profile, created = UserSecurityProfile.objects.get_or_create(user=user)
    if created:
        print("보안 프로필을 생성했습니다.")
    
    print("\n=== 슈퍼유저 로그인 정보 ===")
    print(f"사용자 아이디: {SUPERUSER_DATA['username']}")
    print(f"비밀번호: {SUPERUSER_DATA['password']}")
    print(f"이메일: {SUPERUSER_DATA['email']}")
    print("========================")
    print("\n관리자 페이지: http://localhost:8000/admin/")
    print("API 문서: http://localhost:8000/api/docs/")

if __name__ == '__main__':
    create_superuser()