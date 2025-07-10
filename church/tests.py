import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from church.models import Church
from users.models import ChurchUser

User = get_user_model()


@pytest.mark.django_db
class TestChurchAPI:
    """교회 API 테스트"""

    def setup_method(self):
        """테스트 초기 설정"""
        self.client = APIClient()
        
        # 테스트용 교회 생성
        self.church = Church.objects.create(
            name="테스트교회",
            code="TEST001",
            address="서울시 강남구",
            phone="02-1234-5678",
            pastor_name="홍길동 목사님"
        )
        
        # 테스트용 슈퍼관리자 생성
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123"
        )
        
        # 테스트용 교회 관리자 생성
        self.church_admin = User.objects.create_user(
            username="church_admin",
            email="church_admin@test.com",
            password="testpass123"
        )
        ChurchUser.objects.create(
            user=self.church_admin,
            church=self.church,
            role='church_admin',
            name="교회관리자",
            phone="010-1111-2222"
        )

    def test_church_list_unauthorized(self):
        """인증되지 않은 사용자의 교회 목록 조회 차단"""
        url = reverse('church-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_church_list_authorized(self):
        """인증된 사용자의 교회 목록 조회"""
        self.client.force_authenticate(user=self.superuser)
        url = reverse('church-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_church_create_superuser_only(self):
        """슈퍼관리자만 교회 생성 가능"""
        # 교회 관리자로 시도
        self.client.force_authenticate(user=self.church_admin)
        url = reverse('church-list')
        data = {
            "name": "새교회",
            "code": "NEW001",
            "address": "서울시 송파구",
            "phone": "02-9876-5432",
            "pastor_name": "김목사님"
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # 슈퍼관리자로 시도
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == "새교회"

    def test_church_detail_permission(self):
        """교회 상세 조회 권한 테스트"""
        # 다른 교회 관리자 생성
        other_church = Church.objects.create(
            name="다른교회",
            code="OTHER001"
        )
        other_admin = User.objects.create_user(
            username="other_admin",
            email="other@test.com",
            password="testpass123"
        )
        ChurchUser.objects.create(
            user=other_admin,
            church=other_church,
            role='church_admin',
            name="다른관리자"
        )
        
        # 다른 교회 관리자가 접근 시도
        self.client.force_authenticate(user=other_admin)
        url = reverse('church-detail', kwargs={'pk': self.church.id})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # 해당 교회 관리자가 접근
        self.client.force_authenticate(user=self.church_admin)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "테스트교회"

    def test_church_update(self):
        """교회 정보 수정 테스트"""
        self.client.force_authenticate(user=self.church_admin)
        url = reverse('church-detail', kwargs={'pk': self.church.id})
        data = {
            "name": "테스트교회",
            "code": "TEST001",
            "address": "서울시 강남구 수정된 주소",
            "phone": "02-1234-5678",
            "pastor_name": "홍길동 목사님",
            "website": "https://testchurch.com"
        }
        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['address'] == "서울시 강남구 수정된 주소"
        assert response.data['website'] == "https://testchurch.com"

    def test_church_delete_superuser_only(self):
        """슈퍼관리자만 교회 삭제 가능"""
        # 교회 관리자로 시도
        self.client.force_authenticate(user=self.church_admin)
        url = reverse('church-detail', kwargs={'pk': self.church.id})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # 슈퍼관리자로 시도
        self.client.force_authenticate(user=self.superuser)
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 삭제 확인
        assert not Church.objects.filter(id=self.church.id).exists()

    def test_church_code_unique(self):
        """교회 코드 중복 방지 테스트"""
        self.client.force_authenticate(user=self.superuser)
        url = reverse('church-list')
        data = {
            "name": "중복교회",
            "code": "TEST001",  # 이미 존재하는 코드
            "address": "서울시",
            "phone": "02-0000-0000",
            "pastor_name": "담임목사님"
        }
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data