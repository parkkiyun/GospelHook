from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth, TruncYear
from decimal import Decimal
from datetime import date, timedelta
from .models import Offering
from .serializers import (
    OfferingListSerializer,
    OfferingDetailSerializer,
    OfferingCreateSerializer,
    OfferingUpdateSerializer,
    OfferingStatisticsSerializer
)
from church_core.unified_permissions import UnifiedPermission


class OfferingViewSet(viewsets.ModelViewSet):
    """헌금 관리 API ViewSet"""
    resource_name = 'offering'
    queryset = Offering.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['offering_type', 'date', 'member']
    search_fields = ['member__name', 'offering_type']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        """교회별 헌금 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id).select_related(
            'church', 'member', 'recorded_by'
        )

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'list':
            return OfferingListSerializer
        elif self.action == 'create':
            return OfferingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OfferingUpdateSerializer
        return OfferingDetailSerializer

    def get_serializer_context(self):
        """시리얼라이저 컨텍스트에 church_id 추가"""
        context = super().get_serializer_context()
        context['church_id'] = self.kwargs.get('church_id')
        return context

    def perform_create(self, serializer):
        """헌금 기록 생성 시 교회 정보 자동 설정"""
        church_id = self.kwargs.get('church_id')
        serializer.save(church_id=church_id, recorded_by=self.request.user)

    # create, update, destroy는 UnifiedPermission에서 처리합니다.

    @action(detail=False, methods=['get'])
    def statistics(self, request, church_id=None):
        """헌금 통계 (관리자 전용)"""
        # UnifiedPermission에서 권한 확인
        queryset = self.get_queryset()
        
        # 기간 필터링
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # 기본 통계
        total_stats = queryset.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id'),
            average_amount=Avg('amount')
        )
        
        # 헌금 유형별 통계
        offering_type_stats = queryset.values('offering_type').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('-total_amount')
        
        # 월별 통계
        monthly_stats = queryset.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        # None 값 처리
        for key, value in total_stats.items():
            if value is None:
                total_stats[key] = Decimal('0.00') if 'amount' in key else 0
        
        statistics_data = {
            'total_amount': total_stats['total_amount'],
            'total_count': total_stats['total_count'],
            'average_amount': total_stats['average_amount'],
            'offering_type_stats': list(offering_type_stats),
            'monthly_stats': list(monthly_stats)
        }
        
        return Response(statistics_data)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request, church_id=None):
        """월별 헌금 요약"""
        # UnifiedPermission에서 권한 확인
        year = request.query_params.get('year', date.today().year)
        month = request.query_params.get('month', date.today().month)
        
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return Response(
                {"detail": "올바른 연도와 월을 입력해주세요."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            date__year=year,
            date__month=month
        )
        
        # 월별 통계
        monthly_stats = queryset.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id'),
            average_amount=Avg('amount')
        )
        
        # 헌금 유형별 통계
        type_stats = queryset.values('offering_type').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('-total_amount')
        
        # 일별 통계
        daily_stats = queryset.values('date').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('date')
        
        # None 값 처리
        for key, value in monthly_stats.items():
            if value is None:
                monthly_stats[key] = Decimal('0.00') if 'amount' in key else 0
        
        return Response({
            'year': year,
            'month': month,
            'summary': monthly_stats,
            'type_statistics': list(type_stats),
            'daily_statistics': list(daily_stats)
        })

    @action(detail=False, methods=['get'])
    def yearly_summary(self, request, church_id=None):
        """연도별 헌금 요약"""
        # UnifiedPermission에서 권한 확인
        year = request.query_params.get('year', date.today().year)
        
        try:
            year = int(year)
        except ValueError:
            return Response(
                {"detail": "올바른 연도를 입력해주세요."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(date__year=year)
        
        # 연도별 통계
        yearly_stats = queryset.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id'),
            average_amount=Avg('amount')
        )
        
        # 월별 통계
        monthly_stats = queryset.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        # 헌금 유형별 통계
        type_stats = queryset.values('offering_type').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('-total_amount')
        
        # None 값 처리
        for key, value in yearly_stats.items():
            if value is None:
                yearly_stats[key] = Decimal('0.00') if 'amount' in key else 0
        
        return Response({
            'year': year,
            'summary': yearly_stats,
            'monthly_statistics': list(monthly_stats),
            'type_statistics': list(type_stats)
        })

    @action(detail=False, methods=['get'])
    def recent(self, request, church_id=None):
        """최근 헌금 기록 (최근 30일)"""
        recent_date = date.today() - timedelta(days=30)
        queryset = self.get_queryset().filter(date__gte=recent_date)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request, church_id=None):
        """헌금 유형별 목록"""
        offering_type = request.query_params.get('type')
        if not offering_type:
            return Response(
                {"detail": "헌금 유형을 지정해주세요."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(offering_type=offering_type)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def member_summary(self, request, church_id=None):
        """교인별 헌금 요약 (관리자 전용)"""
        # UnifiedPermission에서 권한 확인
        # 기간 필터링
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.get_queryset().filter(member__isnull=False)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # 교인별 통계
        member_stats = queryset.values(
            'member__name', 'member__id'
        ).annotate(
            total_amount=Sum('amount'),
            count=Count('id'),
            average_amount=Avg('amount')
        ).order_by('-total_amount')
        
        return Response({
            'member_statistics': list(member_stats)
        })
