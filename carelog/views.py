from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import CareLog
from .serializers import CareLogSerializer, CareLogListSerializer, CareLogCreateSerializer
from church_core.roles import SystemRole, Permission
from users.models import ChurchUser


class CareLogViewSet(viewsets.ModelViewSet):
    """생활소식/심방기록 ViewSet"""
    queryset = CareLog.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'date']
    search_fields = ['content', 'member__name']
    ordering = ['-date']

    def get_serializer_class(self):
        if self.action == 'list':
            return CareLogListSerializer
        elif self.action == 'create':
            return CareLogCreateSerializer
        return CareLogSerializer

    def get_queryset(self):
        user = self.request.user
        church_id = self.kwargs.get('church_id')
        
        if user.is_superuser:
            queryset = self.queryset
        else:
            user_churches = user.church_users.values_list('church', flat=True)
            queryset = self.queryset.filter(church__in=user_churches)
        
        if church_id:
            queryset = queryset.filter(church_id=church_id)
        
        return queryset

    def perform_create(self, serializer):
        church_id = self.kwargs.get('church_id')
        church_user = self.request.user.church_users.filter(church_id=church_id).first()
        
        if church_user:
            serializer.save(
                church=church_user.church,
                created_by=self.request.user
            )
        else:
            serializer.save(created_by=self.request.user)

    def check_permission(self, permission_name):
        """권한 확인 헬퍼 메서드"""
        user = self.request.user
        if user.is_superuser:
            return True
        
        church_id = self.kwargs.get('church_id')
        church_user = user.church_users.filter(church_id=church_id).first()
        if church_user:
            return church_user.has_permission(permission_name)
        return False

    def create(self, request, *args, **kwargs):
        """생활소식/심방기록 생성"""
        if not self.check_permission(Permission.CARELOG_CREATE):
            return Response(
                {"detail": "생활소식/심방기록 생성 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """생활소식/심방기록 수정"""
        if not self.check_permission(Permission.CARELOG_UPDATE):
            return Response(
                {"detail": "생활소식/심방기록 수정 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """생활소식/심방기록 삭제"""
        if not self.check_permission(Permission.CARELOG_DELETE):
            return Response(
                {"detail": "생활소식/심방기록 삭제 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """생활소식/심방기록 통계"""
        queryset = self.get_queryset()
        
        # 기본 통계
        total_logs = queryset.count()
        today_logs = queryset.filter(date=date.today()).count()
        this_week_logs = queryset.filter(
            date__gte=date.today() - timedelta(days=7)
        ).count()
        
        # 유형별 통계
        type_stats = {}
        for log_type in CareLog.CareLogType.values:
            count = queryset.filter(type=log_type).count()
            if count > 0:
                type_stats[log_type] = count
        
        # 최근 기록
        recent_logs = CareLogListSerializer(
            queryset.order_by('-date')[:5], 
            many=True
        ).data
        
        return Response({
            'total_logs': total_logs,
            'today_logs': today_logs,
            'this_week_logs': this_week_logs,
            'type_stats': type_stats,
            'recent_logs': recent_logs
        })

    @action(detail=False, methods=['get'])
    def by_member(self, request):
        """교인별 생활소식/심방기록 조회"""
        member_id = request.query_params.get('member_id')
        if not member_id:
            return Response(
                {"detail": "member_id 파라미터가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = self.get_queryset().filter(member_id=member_id)
        
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = CareLogListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CareLogListSerializer(logs, many=True)
        return Response(serializer.data)
