from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import date, timedelta, datetime
from .models import Attendance, AttendanceTemplate
from .serializers import (
    AttendanceSerializer, AttendanceListSerializer, AttendanceCreateSerializer,
    AttendanceBulkCreateSerializer, AttendanceStatsSerializer,
    AttendanceTemplateSerializer, AttendanceTemplateListSerializer
)
from church_core.roles import SystemRole, Permission
from users.models import ChurchUser


class AttendanceViewSet(viewsets.ModelViewSet):
    """출석 관리 API ViewSet"""
    queryset = Attendance.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'worship_type', 'group', 'date']
    search_fields = ['member__name', 'member__member_code', 'notes']
    ordering_fields = ['date', 'member__name', 'worship_type', 'arrival_time']
    ordering = ['-date', 'member__name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AttendanceListSerializer
        elif self.action == 'create':
            return AttendanceCreateSerializer
        elif self.action == 'bulk_create':
            return AttendanceBulkCreateSerializer
        elif self.action == 'statistics':
            return AttendanceStatsSerializer
        return AttendanceSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        
        # 사용자가 속한 교회의 출석 기록만 조회
        user_churches = user.church_users.values_list('church', flat=True)
        return self.queryset.filter(church__in=user_churches)
    
    def perform_create(self, serializer):
        """출석 기록 생성 시 추가 처리"""
        church_user = self.request.user.church_users.first()
        if church_user:
            serializer.save(
                church=church_user.church,
                recorded_by=self.request.user
            )
        else:
            serializer.save(recorded_by=self.request.user)
    
    def check_permission(self, permission_name):
        """권한 확인 헬퍼 메서드"""
        user = self.request.user
        if user.is_superuser:
            return True
        
        church_user = user.church_users.first()
        if church_user:
            return church_user.has_permission(permission_name)
        return False
    
    def create(self, request, *args, **kwargs):
        """출석 기록 생성"""
        if not self.check_permission(Permission.ATTENDANCE_CREATE):
            return Response(
                {"detail": "출석 기록 생성 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """출석 기록 수정"""
        if not self.check_permission(Permission.ATTENDANCE_UPDATE):
            return Response(
                {"detail": "출석 기록 수정 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """출석 기록 삭제"""
        if not self.check_permission(Permission.ATTENDANCE_DELETE):
            return Response(
                {"detail": "출석 기록 삭제 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """대량 출석 기록 생성"""
        if not self.check_permission(Permission.ATTENDANCE_CREATE):
            return Response(
                {"detail": "출석 기록 생성 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AttendanceBulkCreateSerializer(data=request.data)
        if serializer.is_valid():
            date_value = serializer.validated_data['date']
            worship_type = serializer.validated_data['worship_type']
            group_id = serializer.validated_data.get('group_id')
            attendances_data = serializer.validated_data['attendances']
            
            church_user = request.user.church_users.first()
            if not church_user:
                return Response(
                    {"detail": "교회에 속하지 않은 사용자입니다."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            created_attendances = []
            errors = []
            
            for attendance_data in attendances_data:
                try:
                    from members.models import Member
                    member = Member.objects.get(
                        id=attendance_data['member_id'],
                        church=church_user.church
                    )
                    
                    # 그룹 정보 (선택적)
                    group = None
                    if group_id:
                        from groups.models import Group
                        group = Group.objects.get(id=group_id, church=church_user.church)
                    
                    attendance, created = Attendance.objects.update_or_create(
                        church=church_user.church,
                        member=member,
                        date=date_value,
                        worship_type=worship_type,
                        defaults={
                            'status': attendance_data['status'],
                            'arrival_time': attendance_data.get('arrival_time'),
                            'departure_time': attendance_data.get('departure_time'),
                            'notes': attendance_data.get('notes', ''),
                            'group': group,
                            'recorded_by': request.user
                        }
                    )
                    
                    if created:
                        created_attendances.append(attendance)
                    
                except Member.DoesNotExist:
                    errors.append(f"멤버 ID {attendance_data['member_id']}: 존재하지 않는 멤버")
                except Exception as e:
                    errors.append(f"멤버 ID {attendance_data['member_id']}: {str(e)}")
            
            return Response({
                'message': f'{len(created_attendances)}개의 출석 기록이 생성되었습니다.',
                'created_count': len(created_attendances),
                'errors': errors
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """출석 통계"""
        queryset = self.get_queryset()
        
        # 날짜 필터링
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                return Response(
                    {"detail": "start_date 형식이 올바르지 않습니다 (YYYY-MM-DD)."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                return Response(
                    {"detail": "end_date 형식이 올바르지 않습니다 (YYYY-MM-DD)."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 기본 통계
        total_records = queryset.count()
        present_count = queryset.filter(status__in=['present', 'late']).count()
        absent_count = queryset.filter(status='absent').count()
        late_count = queryset.filter(status='late').count()
        
        attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
        
        # 예배 종류별 통계
        worship_type_stats = {}
        for worship_type in Attendance.WorshipType.values:
            count = queryset.filter(worship_type=worship_type).count()
            if count > 0:
                worship_type_stats[worship_type] = count
        
        # 주간 통계 (최근 8주)
        today = date.today()
        weekly_stats = []
        
        for i in range(8):
            week_start = today - timedelta(days=today.weekday() + 7 * i)
            week_end = week_start + timedelta(days=6)
            
            week_attendances = queryset.filter(
                date__range=[week_start, week_end]
            )
            
            week_total = week_attendances.count()
            week_present = week_attendances.filter(status__in=['present', 'late']).count()
            week_rate = (week_present / week_total * 100) if week_total > 0 else 0
            
            weekly_stats.append({
                'week': f'{week_start.strftime("%m/%d")} - {week_end.strftime("%m/%d")}',
                'total': week_total,
                'present': week_present,
                'rate': round(week_rate, 1)
            })
        
        return Response({
            'total_records': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'attendance_rate': round(attendance_rate, 1),
            'worship_type_stats': worship_type_stats,
            'weekly_stats': weekly_stats
        })
    
    @action(detail=False, methods=['get'])
    def by_member(self, request):
        """멤버별 출석 기록 조회"""
        member_id = request.query_params.get('member_id')
        if not member_id:
            return Response(
                {"detail": "member_id 파라미터가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(member_id=member_id)
        
        # 날짜 필터링
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                return Response(
                    {"detail": "start_date 형식이 올바르지 않습니다 (YYYY-MM-DD)."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                return Response(
                    {"detail": "end_date 형식이 올바르지 않습니다 (YYYY-MM-DD)."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 페이지네이션 적용
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AttendanceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AttendanceListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """날짜별 출석 기록 조회"""
        target_date = request.query_params.get('date')
        if not target_date:
            return Response(
                {"detail": "date 파라미터가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "date 형식이 올바르지 않습니다 (YYYY-MM-DD)."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(date=target_date)
        
        # 예배 종류 필터링
        worship_type = request.query_params.get('worship_type')
        if worship_type:
            queryset = queryset.filter(worship_type=worship_type)
        
        # 그룹 필터링
        group_id = request.query_params.get('group_id')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        serializer = AttendanceListSerializer(queryset, many=True)
        return Response(serializer.data)


class AttendanceTemplateViewSet(viewsets.ModelViewSet):
    """출석 템플릿 관리 API ViewSet"""
    queryset = AttendanceTemplate.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['worship_type', 'day_of_week', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'day_of_week', 'start_time']
    ordering = ['day_of_week', 'start_time']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AttendanceTemplateListSerializer
        return AttendanceTemplateSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        
        # 사용자가 속한 교회의 템플릿만 조회
        user_churches = user.church_users.values_list('church', flat=True)
        return self.queryset.filter(church__in=user_churches)
    
    def perform_create(self, serializer):
        """템플릿 생성 시 추가 처리"""
        church_user = self.request.user.church_users.first()
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
        
        church_user = user.church_users.first()
        if church_user:
            return church_user.has_permission(permission_name)
        return False
    
    def create(self, request, *args, **kwargs):
        """템플릿 생성"""
        if not self.check_permission(Permission.ATTENDANCE_TEMPLATE_CREATE):
            return Response(
                {"detail": "출석 템플릿 생성 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """템플릿 수정"""
        if not self.check_permission(Permission.ATTENDANCE_TEMPLATE_UPDATE):
            return Response(
                {"detail": "출석 템플릿 수정 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """템플릿 삭제"""
        if not self.check_permission(Permission.ATTENDANCE_TEMPLATE_DELETE):
            return Response(
                {"detail": "출석 템플릿 삭제 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def create_records(self, request, pk=None):
        """템플릿을 사용하여 출석 기록 생성"""
        template = self.get_object()
        target_date = request.data.get('date')
        
        if target_date:
            try:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"detail": "date 형식이 올바르지 않습니다 (YYYY-MM-DD)."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        created_count = template.create_attendance_records(target_date)
        
        return Response({
            'message': f'{created_count}개의 출석 기록이 생성되었습니다.',
            'created_count': created_count,
            'date': target_date or template.get_next_occurrence()
        })