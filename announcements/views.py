from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import Announcement, PushLog
from .serializers import (
    AnnouncementListSerializer, 
    AnnouncementDetailSerializer, 
    AnnouncementCreateSerializer,
    PushLogSerializer
)
from church_core.unified_permissions import UnifiedPermission


class AnnouncementViewSet(viewsets.ModelViewSet):
    """공지사항 관리 API ViewSet"""
    resource_name = 'announcement'
    queryset = Announcement.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['push_enabled', 'created_by']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """교회별 공지사항 필터링 및 권한별 필터링"""
        church_id = self.kwargs.get('church_id')
        queryset = self.queryset.filter(church_id=church_id)
        
        # 사용자 권한에 따른 필터링
        user = self.request.user
        if user.is_superuser:
            return queryset
        
        # 사용자 권한 확인
        try:
            church_user = user.church_users.get(church_id=church_id)
            user_role = church_user.role
            
            # visible_roles가 빈 배열이면 모든 권한에게 표시
            # 아니면 해당 권한이 포함된 공지사항만 표시
            return queryset.filter(
                Q(visible_roles=[]) | Q(visible_roles__contains=[user_role])
            )
        except:
            # 교회 멤버가 아니면 빈 쿼리셋 반환
            return queryset.none()

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'list':
            return AnnouncementListSerializer
        elif self.action in ['create']:
            return AnnouncementCreateSerializer
        return AnnouncementDetailSerializer

    def perform_create(self, serializer):
        """공지사항 생성 시 교회 정보 및 작성자 자동 설정"""
        church_id = self.kwargs.get('church_id')
        serializer.save(church_id=church_id, created_by=self.request.user)

    # create, update, destroy, send_push는 UnifiedPermission에서 처리합니다.

    @action(detail=True, methods=['post'])
    def send_push(self, request, church_id=None, pk=None):
        """공지사항 푸시 알림 발송"""
        announcement = self.get_object()
        if not announcement.push_enabled:
            return Response(
                {"detail": "푸시 알림이 비활성화된 공지사항입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: 실제 푸시 알림 발송 로직 구현
        # 현재는 시뮬레이션
        from users.models import ChurchUser
        church_users = ChurchUser.objects.filter(church_id=church_id)
        
        sent_count = 0
        for church_user in church_users:
            # visible_roles 확인
            if (not announcement.visible_roles or 
                church_user.role in announcement.visible_roles):
                PushLog.objects.create(
                    announcement=announcement,
                    user=church_user.user,
                    status='SENT'
                )
                sent_count += 1
        
        return Response({
            "message": f"{sent_count}명에게 푸시 알림을 발송했습니다.",
            "sent_count": sent_count
        })

    @action(detail=False, methods=['get'])
    def recent(self, request, church_id=None):
        """최근 공지사항 (최근 30일)"""
        recent_date = date.today() - timedelta(days=30)
        queryset = self.get_queryset().filter(created_at__gte=recent_date)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_role(self, request, church_id=None):
        """내 권한으로 볼 수 있는 공지사항만"""
        queryset = self.get_queryset()  # 이미 권한 필터링이 적용됨
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PushLogViewSet(viewsets.ReadOnlyModelViewSet):
    """푸시 알림 로그 조회 API ViewSet"""
    resource_name = 'pushlog'
    queryset = PushLog.objects.all()
    serializer_class = PushLogSerializer
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'announcement']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']

    def get_queryset(self):
        """교회별 푸시 로그 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(
            announcement__church_id=church_id
        ).select_related('announcement', 'user')

    @action(detail=False, methods=['get'])
    def statistics(self, request, church_id=None):
        """푸시 알림 통계"""
        queryset = self.get_queryset()
        
        # 상태별 통계
        status_stats = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # 공지사항별 통계
        announcement_stats = queryset.values(
            'announcement__title'
        ).annotate(
            total_sent=Count('id'),
            read_count=Count('id', filter=Q(status='READ'))
        ).order_by('-total_sent')[:10]
        
        return Response({
            'status_stats': status_stats,
            'top_announcements': announcement_stats,
            'total_logs': queryset.count()
        })
