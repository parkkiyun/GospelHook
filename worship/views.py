from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import WorshipRecord
from .serializers import (
    WorshipRecordListSerializer, 
    WorshipRecordDetailSerializer, 
    WorshipRecordCreateSerializer
)
from church_core.unified_permissions import UnifiedPermission


class WorshipRecordViewSet(viewsets.ModelViewSet):
    """예배 기록 관리 API ViewSet"""
    resource_name = 'worshiprecord'
    queryset = WorshipRecord.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['worship_type', 'date', 'preacher']
    search_fields = ['preacher', 'theme', 'scripture']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        """교회별 예배 기록 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id).prefetch_related('attendees')

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'list':
            return WorshipRecordListSerializer
        elif self.action in ['create']:
            return WorshipRecordCreateSerializer
        return WorshipRecordDetailSerializer

    def perform_create(self, serializer):
        """예배 기록 생성 시 교회 정보 자동 설정"""
        church_id = self.kwargs.get('church_id')
        serializer.save(church_id=church_id, created_by=self.request.user)

    # create, update, destroy는 UnifiedPermission에서 처리합니다.

    @action(detail=False, methods=['get'])
    def statistics(self, request, church_id=None):
        """예배 통계"""
        queryset = self.get_queryset()
        
        # 예배별 통계
        worship_stats = queryset.values('worship_type').annotate(
            count=Count('id'),
            avg_attendees=Count('attendees')
        ).order_by('worship_type')
        
        # 월별 통계 (최근 12개월)
        monthly_stats = []
        for i in range(12):
            target_date = date.today().replace(day=1) - timedelta(days=30*i)
            month_count = queryset.filter(
                date__year=target_date.year,
                date__month=target_date.month
            ).count()
            monthly_stats.append({
                'month': target_date.strftime('%Y-%m'),
                'count': month_count
            })
        
        return Response({
            'worship_type_stats': worship_stats,
            'monthly_stats': monthly_stats[::-1],  # 오래된 순으로 정렬
            'total_records': queryset.count()
        })

    @action(detail=False, methods=['get'])
    def recent(self, request, church_id=None):
        """최근 예배 기록 (최근 30일)"""
        recent_date = date.today() - timedelta(days=30)
        queryset = self.get_queryset().filter(date__gte=recent_date)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_preacher(self, request, church_id=None):
        """설교자별 예배 기록"""
        preacher = request.query_params.get('preacher')
        if not preacher:
            return Response(
                {"detail": "설교자를 지정해주세요."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(preacher__icontains=preacher)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def preachers(self, request, church_id=None):
        """설교자 목록"""
        preachers = self.get_queryset().values_list(
            'preacher', flat=True
        ).distinct().order_by('preacher')
        return Response(list(preachers))