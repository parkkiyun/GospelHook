from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    ReportTemplate, Report, Dashboard, StatisticsSummary,
    ReportSchedule, ExportLog, MinistryReport, 
    MinistryReportTemplate, MinistryReportComment
)
from .serializers import (
    ReportTemplateSerializer, ReportTemplateListSerializer,
    ReportSerializer, ReportListSerializer, ReportCreateSerializer,
    DashboardSerializer, DashboardListSerializer,
    StatisticsSummarySerializer, ReportScheduleSerializer,
    ExportLogSerializer, ExportLogCreateSerializer,
    StatisticsOverviewSerializer, MinistryReportListSerializer,
    MinistryReportDetailSerializer, MinistryReportCreateSerializer,
    MinistryReportUpdateSerializer, MinistryReportTemplateSerializer,
    MinistryReportCommentSerializer, MinistryReportStatusUpdateSerializer
)
from church_core.unified_permissions import UnifiedPermission
from users.models import ChurchUser
from church.models import Church


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """리포트 템플릿 ViewSet"""
    resource_name = 'reporttemplate'
    queryset = ReportTemplate.objects.all()
    permission_classes = [permissions.IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['report_type', 'is_auto_generate', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ReportTemplateListSerializer
        return ReportTemplateSerializer
    
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


class ReportViewSet(viewsets.ModelViewSet):
    """리포트 ViewSet"""
    resource_name = 'report'
    queryset = Report.objects.all()
    permission_classes = [permissions.IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template', 'status']
    search_fields = ['title', 'summary']
    ordering = ['-generated_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ReportListSerializer
        elif self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer
    
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
                generated_by=self.request.user
            )
        else:
            serializer.save(generated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """리포트 재생성"""
        report = self.get_object()
        
        # 리포트 재생성 로직 (비동기 처리 권장)
        report.status = Report.Status.GENERATING
        report.save()
        
        return Response({"message": "리포트 재생성이 시작되었습니다."})


class DashboardViewSet(viewsets.ModelViewSet):
    """대시보드 ViewSet"""
    resource_name = 'dashboard'
    queryset = Dashboard.objects.all()
    permission_classes = [permissions.IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DashboardListSerializer
        return DashboardSerializer
    
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


class StatisticsSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """통계 요약 ViewSet"""
    resource_name = 'statisticssummary'
    queryset = StatisticsSummary.objects.all()
    serializer_class = StatisticsSummarySerializer
    permission_classes = [permissions.IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering = ['-date']
    
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
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """통계 개요"""
        church_id = self.kwargs.get('church_id')
        today = date.today()
        
        # 최근 7일간의 통계
        recent_stats = self.get_queryset().filter(
            date__gte=today - timedelta(days=7)
        ).first()
        
        if not recent_stats:
            return Response({"detail": "통계 데이터가 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        overview_data = {
            'members': {
                'total': recent_stats.total_members,
                'active': recent_stats.active_members,
                'new_today': recent_stats.new_members_today,
                'new_this_month': recent_stats.new_members_this_month,
            },
            'attendance': {
                'sunday': recent_stats.sunday_attendance,
                'wednesday': recent_stats.wednesday_attendance,
                'weekly_total': recent_stats.total_attendance_this_week,
                'rate': recent_stats.attendance_rate,
            },
            'prayers': {
                'total': recent_stats.total_prayers,
                'active': recent_stats.active_prayers,
                'answered_today': recent_stats.answered_prayers_today,
            },
            'groups': {
                'total': recent_stats.total_groups,
                'active': recent_stats.active_groups,
            },
            'offerings': {
                'today': float(recent_stats.total_offerings_today),
                'this_month': float(recent_stats.total_offerings_this_month),
            },
            'recent_activities': []  # TODO: 최근 활동 데이터 추가
        }
        
        serializer = StatisticsOverviewSerializer(overview_data)
        return Response(serializer.data)


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """리포트 스케줄 ViewSet"""
    resource_name = 'reportschedule'
    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active', 'last_success']
    ordering = ['next_run']
    
    def get_queryset(self):
        user = self.request.user
        church_id = self.kwargs.get('church_id')
        
        if user.is_superuser:
            queryset = self.queryset
        else:
            # 스케줄은 템플릿을 통해 교회별로 필터링
            user_churches = user.church_users.values_list('church', flat=True)
            queryset = self.queryset.filter(template__church__in=user_churches)
        
        if church_id:
            queryset = queryset.filter(template__church_id=church_id)
        
        return queryset


class ExportLogViewSet(viewsets.ModelViewSet):
    """내보내기 로그 ViewSet"""
    resource_name = 'exportlog'
    queryset = ExportLog.objects.all()
    permission_classes = [permissions.IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['export_type', 'status']
    ordering = ['-requested_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ExportLogCreateSerializer
        return ExportLogSerializer
    
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
                requested_by=self.request.user
            )
        else:
            serializer.save(requested_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_exports(self, request):
        """내 내보내기 로그 조회"""
        user = request.user
        exports = self.get_queryset().filter(requested_by=user)
        
        page = self.paginate_queryset(exports)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(exports, many=True)
        return Response(serializer.data)


class MinistryReportViewSet(viewsets.ModelViewSet):
    """사역 보고서 ViewSet"""
    resource_name = 'ministryreport'
    permission_classes = [permissions.IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'priority', 'reporter', 'department', 'volunteer_role']
    search_fields = ['title', 'summary', 'content']
    ordering_fields = ['report_date', 'created_at', 'updated_at', 'submitted_at']
    ordering = ['-report_date', '-created_at']

    def get_church(self):
        """교회 ID 가져오기"""
        church_id = self.kwargs.get('church_id')
        return Church.objects.get(id=church_id)

    def get_queryset(self):
        queryset = MinistryReport.objects.filter(church=self.get_church()).select_related(
            'reporter', 'department', 'volunteer_role', 'reviewer'
        ).prefetch_related('comments__author')
        
        # UnifiedPermission이 객체 수준에서 처리
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return MinistryReportListSerializer
        elif self.action in ['create']:
            return MinistryReportCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MinistryReportUpdateSerializer
        elif self.action == 'update_status':
            return MinistryReportStatusUpdateSerializer
        else:
            return MinistryReportDetailSerializer

    def perform_create(self, serializer):
        """보고서 생성"""
        serializer.save(
            church=self.get_church(),
            reporter=self.request.user.church_user
        )

    # perform_update는 UnifiedPermission에서 처리

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """보고서 상태 변경"""
        report = self.get_object()
        serializer = MinistryReportStatusUpdateSerializer(
            report, data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'status': report.status,
            'message': f'보고서 상태가 {report.get_status_display()}로 변경되었습니다.'
        })

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """보고서 제출"""
        report = self.get_object()
        
        if report.reporter != request.user.church_user:
            return Response(
                {'error': '본인 작성 보고서만 제출할 수 있습니다.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if report.status != MinistryReport.Status.DRAFT:
            return Response(
                {'error': '임시저장 상태의 보고서만 제출할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.submit()
        return Response({
            'status': 'submitted',
            'message': '보고서가 제출되었습니다.'
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """보고서 승인"""
        report = self.get_object()
        comments = request.data.get('comments', '')
        
        if report.status not in [MinistryReport.Status.SUBMITTED, MinistryReport.Status.REVIEWED]:
            return Response(
                {'error': '승인할 수 없는 상태입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.approve(request.user.church_user, comments)
        return Response({
            'status': 'approved',
            'message': '보고서가 승인되었습니다.'
        })

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """보고서 반려"""
        report = self.get_object()
        comments = request.data.get('comments', '')
        
        if not comments:
            return Response(
                {'error': '반려 사유를 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if report.status not in [MinistryReport.Status.SUBMITTED, MinistryReport.Status.REVIEWED]:
            return Response(
                {'error': '반려할 수 없는 상태입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.reject(request.user.church_user, comments)
        return Response({
            'status': 'rejected',
            'message': '보고서가 반려되었습니다.'
        })

    @action(detail=False, methods=['get'])
    def my_reports(self, request):
        """내가 작성한 보고서 목록"""
        queryset = self.get_queryset().filter(reporter=request.user.church_user)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MinistryReportListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MinistryReportListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_reviews(self, request):
        """검토 대기 보고서 목록 (관리자용)"""
        # UnifiedPermission에서 권한 확인
        queryset = self.get_queryset().filter(
            status__in=[MinistryReport.Status.SUBMITTED, MinistryReport.Status.REVIEWED]
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MinistryReportListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MinistryReportListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """보고서 통계"""
        church = self.get_church()
        queryset = MinistryReport.objects.filter(church=church)
        
        stats = {
            'total_reports': queryset.count(),
            'by_status': {
                status_code: queryset.filter(status=status_code).count()
                for status_code, _ in MinistryReport.Status.choices
            },
            'by_category': {
                category_code: queryset.filter(category=category_code).count()
                for category_code, _ in MinistryReport.ReportCategory.choices
            },
            'this_month': queryset.filter(
                report_date__year=timezone.now().year,
                report_date__month=timezone.now().month
            ).count(),
            'recent_activity': queryset.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).count()
        }
        
        return Response(stats)


class MinistryReportCommentViewSet(viewsets.ModelViewSet):
    """사역 보고서 댓글 ViewSet"""
    resource_name = 'ministryreportcomment'
    serializer_class = MinistryReportCommentSerializer
    permission_classes = [permissions.IsAuthenticated, UnifiedPermission]

    def get_queryset(self):
        report_id = self.kwargs.get('report_pk')
        return MinistryReportComment.objects.filter(
            report_id=report_id,
            is_deleted=False
        ).select_related('author', 'parent').order_by('created_at')

    def perform_create(self, serializer):
        """댓글 생성"""
        report_id = self.kwargs.get('report_pk')
        serializer.save(
            report_id=report_id,
            author=self.request.user.church_user
        )

    # perform_destroy는 UnifiedPermission에서 처리


class MinistryReportTemplateViewSet(viewsets.ModelViewSet):
    """사역 보고서 템플릿 ViewSet"""
    serializer_class = MinistryReportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'auto_create']
    search_fields = ['name', 'description']
    ordering = ['name']

    def get_church(self):
        """교회 ID 가져오기"""
        church_id = self.kwargs.get('church_id')
        return Church.objects.get(id=church_id)

    def get_queryset(self):
        return MinistryReportTemplate.objects.filter(
            church=self.get_church()
        ).prefetch_related('target_roles', 'target_groups', 'default_reviewers')

    @action(detail=True, methods=['post'])
    def create_report(self, request, pk=None):
        """템플릿으로부터 보고서 생성"""
        template = self.get_object()
        report_date = request.data.get('report_date', timezone.now().date())
        
        report = template.create_report_for_user(
            request.user.church_user,
            report_date
        )
        
        serializer = MinistryReportDetailSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
