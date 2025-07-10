from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Church
from .serializers import (
    ChurchSerializer, ChurchListSerializer, ChurchCreateSerializer,
    ChurchSettingsSerializer
)
from church_core.roles import SystemRole
from users.models import ChurchUser


class ChurchViewSet(viewsets.ModelViewSet):
    """교회 관리 API ViewSet"""
    queryset = Church.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'denomination']
    search_fields = ['name', 'code', 'address', 'pastor_name']
    ordering_fields = ['name', 'created_at', 'member_count']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ChurchListSerializer
        elif self.action == 'create':
            return ChurchCreateSerializer
        elif self.action == 'church_settings':
            return ChurchSettingsSerializer
        return ChurchSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        
        # 사용자가 속한 교회들만 조회
        user_churches = user.church_users.values_list('church', flat=True)
        return self.queryset.filter(id__in=user_churches)
    
    def perform_create(self, serializer):
        """교회 생성 시 추가 처리"""
        church = serializer.save()
        
        # 생성자를 해당 교회의 관리자로 설정
        if not self.request.user.is_superuser:
            ChurchUser.objects.create(
                user=self.request.user,
                church=church,
                role=SystemRole.CHURCH_ADMIN,
                name=self.request.user.username,
                phone=self.request.user.phone
            )
    
    def create(self, request, *args, **kwargs):
        """교회 생성 권한 확인"""
        # 슈퍼관리자만 교회 생성 가능
        if not request.user.is_superuser:
            return Response(
                {"detail": "교회 생성 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """교회 정보 수정 권한 확인"""
        church = self.get_object()
        user = request.user
        
        if not user.is_superuser:
            # 해당 교회의 관리자인지 확인
            try:
                church_user = ChurchUser.objects.get(user=user, church=church)
                if church_user.role not in [SystemRole.SUPER_ADMIN, SystemRole.CHURCH_ADMIN]:
                    return Response(
                        {"detail": "교회 정보 수정 권한이 없습니다."}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except ChurchUser.DoesNotExist:
                return Response(
                    {"detail": "해당 교회에 속하지 않습니다."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """교회 삭제는 슈퍼관리자만 가능"""
        if not request.user.is_superuser:
            return Response(
                {"detail": "교회 삭제 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get', 'patch'])
    def church_settings(self, request, pk=None):
        """교회 설정 관리"""
        church = self.get_object()
        
        if request.method == 'GET':
            serializer = ChurchSettingsSerializer(church)
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
            serializer = ChurchSettingsSerializer(church, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """교회 통계 정보"""
        church = self.get_object()
        
        # 기본 통계 계산
        total_members = church.member_count
        active_members = church.members.filter(status='active').count()
        groups_count = church.groups.filter(is_active=True).count()
        
        stats = {
            'total_members': total_members,
            'active_members': active_members,
            'inactive_members': total_members - active_members,
            'groups_count': groups_count,
            'capacity_usage': round((total_members / church.max_members) * 100, 2) if church.max_members else 0,
        }
        
        return Response(stats)
