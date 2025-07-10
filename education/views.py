from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import EducationProgram, EducationRegistration
from .serializers import (
    EducationProgramListSerializer,
    EducationProgramDetailSerializer,
    EducationProgramCreateSerializer,
    EducationRegistrationSerializer,
    EducationRegistrationCreateSerializer
)
from church_core.unified_permissions import UnifiedPermission


class EducationProgramViewSet(viewsets.ModelViewSet):
    """교육 프로그램 관리 API ViewSet"""
    resource_name = 'educationprogram'
    queryset = EducationProgram.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'target_roles']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'registration_deadline', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        """교회별 교육 프로그램 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id).select_related('church')

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'list':
            return EducationProgramListSerializer
        elif self.action in ['create']:
            return EducationProgramCreateSerializer
        return EducationProgramDetailSerializer

    def perform_create(self, serializer):
        """교육 프로그램 생성 시 교회 정보 자동 설정"""
        church_id = self.kwargs.get('church_id')
        serializer.save(church_id=church_id, created_by=self.request.user)

    # create, update, destroy는 UnifiedPermission에서 처리합니다.

    @action(detail=False, methods=['get'])
    def upcoming(self, request, church_id=None):
        """예정된 교육 프로그램 목록"""
        today = date.today()
        queryset = self.get_queryset().filter(date__gte=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def open_for_registration(self, request, church_id=None):
        """등록 가능한 교육 프로그램 목록"""
        today = date.today()
        queryset = self.get_queryset().filter(registration_deadline__gte=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request, church_id=None):
        """교육 프로그램 통계"""
        # UnifiedPermission에서 권한 확인
        queryset = self.get_queryset()
        today = date.today()
        
        # 기본 통계
        total_programs = queryset.count()
        upcoming_programs = queryset.filter(date__gte=today).count()
        completed_programs = queryset.filter(date__lt=today).count()
        
        # 등록 통계
        total_registrations = EducationRegistration.objects.filter(
            program__church_id=church_id
        ).exclude(status='CANCELED').count()
        
        # 월별 프로그램 수
        monthly_programs = queryset.filter(
            date__year=today.year
        ).extra(
            select={'month': 'EXTRACT(month FROM date)'}
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        return Response({
            'total_programs': total_programs,
            'upcoming_programs': upcoming_programs,
            'completed_programs': completed_programs,
            'total_registrations': total_registrations,
            'monthly_programs': list(monthly_programs)
        })

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None, church_id=None):
        """교육 프로그램 등록"""
        program = self.get_object()
        
        # 등록 가능 여부 확인
        today = date.today()
        if program.registration_deadline < today:
            return Response(
                {"detail": "등록 마감일이 지났습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 정원 확인
        if program.max_people:
            current_count = program.educationregistration_set.exclude(status='CANCELED').count()
            if current_count >= program.max_people:
                return Response(
                    {"detail": "정원이 초과되었습니다."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 사용자의 교회 멤버 정보 가져오기
        try:
            church_user = request.user.church_users.get(church_id=church_id)
            member = church_user.member
        except:
            return Response(
                {"detail": "교회 멤버 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 중복 등록 확인
        if EducationRegistration.objects.filter(
            program=program,
            member=member
        ).exists():
            return Response(
                {"detail": "이미 등록된 프로그램입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 등록 생성
        registration = EducationRegistration.objects.create(
            program=program,
            member=member
        )
        
        serializer = EducationRegistrationSerializer(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def cancel_registration(self, request, pk=None, church_id=None):
        """교육 프로그램 등록 취소"""
        program = self.get_object()
        
        # 사용자의 교회 멤버 정보 가져오기
        try:
            church_user = request.user.church_users.get(church_id=church_id)
            member = church_user.member
        except:
            return Response(
                {"detail": "교회 멤버 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 등록 정보 찾기
        try:
            registration = EducationRegistration.objects.get(
                program=program,
                member=member
            )
        except EducationRegistration.DoesNotExist:
            return Response(
                {"detail": "등록 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 등록 취소
        registration.status = 'CANCELED'
        registration.save()
        
        return Response({"detail": "등록이 취소되었습니다."})


class EducationRegistrationViewSet(viewsets.ModelViewSet):
    """교육 등록 관리 API ViewSet"""
    resource_name = 'educationregistration'
    queryset = EducationRegistration.objects.all()
    serializer_class = EducationRegistrationSerializer
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'program']
    search_fields = ['member__name', 'program__title']
    ordering_fields = ['registered_at']
    ordering = ['-registered_at']

    def get_queryset(self):
        """교회별 교육 등록 필터링"""
        church_id = self.kwargs.get('church_id')
        queryset = self.queryset.filter(program__church_id=church_id).select_related(
            'program', 'member'
        )
        
        # UnifiedPermission이 객체 수준 권한을 처리하므로, 수동 필터링 제거
        return queryset

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'create':
            return EducationRegistrationCreateSerializer
        return EducationRegistrationSerializer

    def perform_create(self, serializer):
        """교육 등록 생성 시 멤버 정보 자동 설정"""
        church_id = self.kwargs.get('church_id')
        try:
            church_user = self.request.user.church_users.get(church_id=church_id)
            member = church_user.member
            serializer.save(member=member)
        except:
            raise serializers.ValidationError("교회 멤버 정보를 찾을 수 없습니다.")

    # update, destroy는 UnifiedPermission에서 객체 소유권 등을 확인하여 처리합니다.

    @action(detail=False, methods=['get'])
    def my_registrations(self, request, church_id=None):
        """내 교육 등록 목록"""
        try:
            church_user = request.user.church_users.get(church_id=church_id)
            member = church_user.member
        except:
            return Response(
                {"detail": "교회 멤버 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(member=member)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request, church_id=None):
        """교육 등록 통계 (관리자 전용)"""
        # UnifiedPermission에서 권한 확인
        queryset = self.get_queryset()
        
        # 상태별 통계
        status_stats = queryset.values('status').annotate(count=Count('id'))
        
        # 프로그램별 등록 통계
        program_stats = queryset.values(
            'program__title'
        ).annotate(count=Count('id')).order_by('-count')[:10]
        
        return Response({
            'status_statistics': list(status_stats),
            'top_programs': list(program_stats)
        })