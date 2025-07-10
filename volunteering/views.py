from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import VolunteerApplication, VolunteerRole, VolunteerAssignment, DEFAULT_VOLUNTEER_ROLES
from .serializers import (
    VolunteerApplicationListSerializer,
    VolunteerApplicationDetailSerializer,
    VolunteerApplicationCreateSerializer,
    VolunteerApplicationUpdateSerializer,
    VolunteerRoleSerializer,
    VolunteerRoleCreateSerializer,
    VolunteerAssignmentSerializer,
    VolunteerAssignmentCreateSerializer,
    VolunteerRoleTemplateSerializer
)
from church_core.unified_permissions import UnifiedPermission


class VolunteerApplicationViewSet(viewsets.ModelViewSet):
    """봉사 신청 관리 API ViewSet"""
    resource_name = 'volunteerapplication'
    queryset = VolunteerApplication.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'target_roles']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        """교회별 봉사 신청 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id).select_related('church').prefetch_related('applicants')

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'list':
            return VolunteerApplicationListSerializer
        elif self.action == 'create':
            return VolunteerApplicationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return VolunteerApplicationUpdateSerializer
        return VolunteerApplicationDetailSerializer

    def get_serializer_context(self):
        """시리얼라이저 컨텍스트에 church_id 추가"""
        context = super().get_serializer_context()
        context['church_id'] = self.kwargs.get('church_id')
        return context

    def perform_create(self, serializer):
        """봉사 신청 생성 시 교회 정보 자동 설정"""
        church_id = self.kwargs.get('church_id')
        serializer.save(church_id=church_id)

    # create, update, destroy는 UnifiedPermission에서 처리합니다.

    @action(detail=False, methods=['get'])
    def upcoming(self, request, church_id=None):
        """예정된 봉사 신청 목록"""
        today = date.today()
        queryset = self.get_queryset().filter(date__gte=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def open_for_application(self, request, church_id=None):
        """신청 가능한 봉사 목록"""
        today = date.today()
        queryset = self.get_queryset().filter(date__gte=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_applications(self, request, church_id=None):
        """내가 신청한 봉사 목록"""
        try:
            church_user = request.user.church_users.get(church_id=church_id)
            member = church_user.member
        except:
            return Response(
                {"detail": "교회 멤버 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(applicants=member)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None, church_id=None):
        """봉사 신청하기"""
        volunteer_application = self.get_object()
        
        # 신청 가능 여부 확인
        today = date.today()
        if volunteer_application.date < today:
            return Response(
                {"detail": "이미 지난 봉사입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 정원 확인
        if volunteer_application.max_people:
            if volunteer_application.applicants.count() >= volunteer_application.max_people:
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
        
        # 중복 신청 확인
        if volunteer_application.applicants.filter(id=member.id).exists():
            return Response(
                {"detail": "이미 신청한 봉사입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 신청 추가
        volunteer_application.applicants.add(member)
        
        return Response({"detail": "봉사 신청이 완료되었습니다."})

    @action(detail=True, methods=['delete'])
    def cancel_application(self, request, pk=None, church_id=None):
        """봉사 신청 취소"""
        volunteer_application = self.get_object()
        
        # 사용자의 교회 멤버 정보 가져오기
        try:
            church_user = request.user.church_users.get(church_id=church_id)
            member = church_user.member
        except:
            return Response(
                {"detail": "교회 멤버 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 신청 여부 확인
        if not volunteer_application.applicants.filter(id=member.id).exists():
            return Response(
                {"detail": "신청하지 않은 봉사입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 신청 취소
        volunteer_application.applicants.remove(member)
        
        return Response({"detail": "봉사 신청이 취소되었습니다."})

    @action(detail=False, methods=['get'])
    def statistics(self, request, church_id=None):
        """봉사 신청 통계 (관리자 전용)"""
        # UnifiedPermission에서 권한 확인
        queryset = self.get_queryset()
        today = date.today()
        
        # 기본 통계
        total_applications = queryset.count()
        upcoming_applications = queryset.filter(date__gte=today).count()
        completed_applications = queryset.filter(date__lt=today).count()
        
        # 신청자 통계
        total_applicants = sum(application.applicants.count() for application in queryset)
        
        # 월별 봉사 수
        monthly_applications = queryset.filter(
            date__year=today.year
        ).extra(
            select={'month': 'EXTRACT(month FROM date)'}
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        # 인기 봉사 TOP 5
        popular_applications = queryset.annotate(
            applicant_count=Count('applicants')
        ).order_by('-applicant_count')[:5]
        
        popular_data = [{
            'title': app.title,
            'date': app.date,
            'applicant_count': app.applicant_count
        } for app in popular_applications]
        
        return Response({
            'total_applications': total_applications,
            'upcoming_applications': upcoming_applications,
            'completed_applications': completed_applications,
            'total_applicants': total_applicants,
            'monthly_applications': list(monthly_applications),
            'popular_applications': popular_data
        })

    @action(detail=True, methods=['get'])
    def applicants(self, request, pk=None, church_id=None):
        """봉사 신청자 목록 (관리자 전용)"""
        # UnifiedPermission에서 권한 확인
        volunteer_application = self.get_object()
        applicants = volunteer_application.applicants.all()
        
        applicant_data = [{
            'id': applicant.id,
            'name': applicant.name,
            'phone': applicant.phone,
            'email': applicant.email,
            'role': applicant.role if hasattr(applicant, 'role') else None
        } for applicant in applicants]
        
        return Response({
            'volunteer_application': volunteer_application.title,
            'applicants': applicant_data,
            'total_count': len(applicant_data)
        })

    @action(detail=True, methods=['post'])
    def manage_applicant(self, request, pk=None, church_id=None):
        """봉사 신청자 관리 (관리자 전용) - 강제 추가/제거"""
        # UnifiedPermission에서 권한 확인
        volunteer_application = self.get_object()
        member_id = request.data.get('member_id')
        action_type = request.data.get('action')  # 'add' or 'remove'
        
        if not member_id or not action_type:
            return Response(
                {"detail": "member_id와 action을 지정해주세요."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 멤버 존재 확인
        try:
            from members.models import Member
            member = Member.objects.get(id=member_id, church_id=church_id)
        except Member.DoesNotExist:
            return Response(
                {"detail": "해당 교인을 찾을 수 없습니다."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if action_type == 'add':
            if volunteer_application.applicants.filter(id=member.id).exists():
                return Response(
                    {"detail": "이미 신청한 교인입니다."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            volunteer_application.applicants.add(member)
            return Response({"detail": f"{member.name}님이 봉사에 추가되었습니다."})
        
        elif action_type == 'remove':
            if not volunteer_application.applicants.filter(id=member.id).exists():
                return Response(
                    {"detail": "신청하지 않은 교인입니다."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            volunteer_application.applicants.remove(member)
            return Response({"detail": f"{member.name}님이 봉사에서 제거되었습니다."})
        
        else:
            return Response(
                {"detail": "action은 'add' 또는 'remove'여야 합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class VolunteerRoleViewSet(viewsets.ModelViewSet):
    """봉사 역할 관리 API ViewSet"""
    resource_name = 'volunteerrole'
    queryset = VolunteerRole.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'required_level', 'requires_training', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'category', 'created_at']
    ordering = ['category', 'name']

    def get_queryset(self):
        """교회별 봉사 역할 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id).prefetch_related('target_groups', 'volunteer_assignments')

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'create':
            return VolunteerRoleCreateSerializer
        return VolunteerRoleSerializer

    def get_serializer_context(self):
        """시리얼라이저 컨텍스트에 church_id 추가"""
        context = super().get_serializer_context()
        context['church_id'] = self.kwargs.get('church_id')
        return context

    # create, update, destroy는 UnifiedPermission에서 처리합니다.

    @action(detail=False, methods=['get'])
    def categories(self, request, church_id=None):
        """봉사 역할 카테고리 목록"""
        categories = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in VolunteerRole.RoleCategory.choices
        ]
        return Response(categories)

    @action(detail=False, methods=['get'])
    def required_levels(self, request, church_id=None):
        """봉사 역할 요구 수준 목록"""
        levels = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in VolunteerRole.RequiredLevel.choices
        ]
        return Response(levels)

    @action(detail=False, methods=['get'])
    def templates(self, request, church_id=None):
        """기본 봉사 역할 템플릿 목록"""
        return Response(DEFAULT_VOLUNTEER_ROLES)

    @action(detail=False, methods=['post'])
    def create_from_template(self, request, church_id=None):
        """템플릿으로부터 봉사 역할 생성 (관리자 권한 필요)"""
        # UnifiedPermission에서 권한 확인
        template_codes = request.data.get('template_codes', [])
        if not template_codes:
            return Response(
                {"detail": "생성할 템플릿 코드를 지정해주세요."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        created_roles = []
        errors = []

        for template_code in template_codes:
            # 템플릿 찾기
            template = next((t for t in DEFAULT_VOLUNTEER_ROLES if t['code'] == template_code), None)
            if not template:
                errors.append(f"템플릿을 찾을 수 없습니다: {template_code}")
                continue

            # 중복 검사
            if VolunteerRole.objects.filter(church_id=church_id, code=template_code).exists():
                errors.append(f"이미 존재하는 역할입니다: {template['name']}")
                continue

            # 역할 생성
            try:
                serializer = VolunteerRoleTemplateSerializer(
                    data=template, 
                    context=self.get_serializer_context()
                )
                if serializer.is_valid():
                    role = serializer.save()
                    created_roles.append({
                        'id': role.id,
                        'name': role.name,
                        'code': role.code,
                        'category': role.category
                    })
                else:
                    errors.append(f"템플릿 검증 실패: {template['name']} - {serializer.errors}")
            except Exception as e:
                errors.append(f"템플릿 생성 실패: {template['name']} - {str(e)}")

        return Response({
            'created_roles': created_roles,
            'errors': errors,
            'total_created': len(created_roles)
        })

    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None, church_id=None):
        """특정 봉사 역할의 할당 목록"""
        volunteer_role = self.get_object()
        assignments = volunteer_role.volunteer_assignments.filter(is_active=True)
        serializer = VolunteerAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request, church_id=None):
        """봉사 역할 통계 (관리자 전용)"""
        # UnifiedPermission에서 권한 확인
        queryset = self.get_queryset()
        
        # 기본 통계
        total_roles = queryset.count()
        active_roles = queryset.filter(is_active=True).count()
        
        # 카테고리별 통계
        category_stats = queryset.values('category').annotate(
            count=Count('id')
        ).order_by('category')
        
        # 할당 통계
        total_assignments = VolunteerAssignment.objects.filter(
            volunteer_role__church_id=church_id,
            is_active=True
        ).count()
        
        # 인기 역할 TOP 5
        popular_roles = queryset.annotate(
            assignment_count=Count('volunteer_assignments', filter=Q(volunteer_assignments__is_active=True))
        ).order_by('-assignment_count')[:5]
        
        popular_data = [{
            'name': role.name,
            'category': role.get_category_display(),
            'assignment_count': role.assignment_count
        } for role in popular_roles]

        return Response({
            'total_roles': total_roles,
            'active_roles': active_roles,
            'total_assignments': total_assignments,
            'category_stats': list(category_stats),
            'popular_roles': popular_data
        })


class VolunteerAssignmentViewSet(viewsets.ModelViewSet):
    """봉사 할당 관리 API ViewSet"""
    resource_name = 'volunteerassignment'
    queryset = VolunteerAssignment.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['volunteer_role', 'is_active', 'approved_by']
    search_fields = ['church_user__name', 'volunteer_role__name', 'notes']
    ordering_fields = ['assigned_date', 'start_date', 'end_date']
    ordering = ['-assigned_date']

    def get_queryset(self):
        """교회별 봉사 할당 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(
            volunteer_role__church_id=church_id
        ).select_related('church_user', 'volunteer_role', 'approved_by')

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'create':
            return VolunteerAssignmentCreateSerializer
        return VolunteerAssignmentSerializer

    # create, update, destroy는 UnifiedPermission에서 처리합니다.

    @action(detail=False, methods=['get'])
    def my_assignments(self, request, church_id=None):
        """내 봉사 할당 목록"""
        try:
            church_user = request.user.church_users.get(church_id=church_id)
        except:
            return Response(
                {"detail": "교회 멤버 정보를 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        assignments = self.get_queryset().filter(church_user=church_user, is_active=True)
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_permissions(self, request, pk=None, church_id=None):
        """봉사 할당의 개별 권한 업데이트 (관리자 권한 필요)"""
        # UnifiedPermission에서 권한 확인
        assignment = self.get_object()
        custom_permissions = request.data.get('custom_permissions', [])
        
        # 권한 유효성 검사 (필요 시)

        assignment.custom_permissions = custom_permissions
        assignment.save()

        serializer = self.get_serializer(assignment)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_role(self, request, church_id=None):
        """봉사 역할별 할당 목록"""
        role_id = request.query_params.get('role_id')
        if not role_id:
            return Response(
                {"detail": "role_id 파라미터가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        assignments = self.get_queryset().filter(volunteer_role_id=role_id, is_active=True)
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request, church_id=None):
        """봉사 할당 통계 (관리자 전용)"""
        # UnifiedPermission에서 권한 확인
        queryset = self.get_queryset()
        
        # 기본 통계
        total_assignments = queryset.count()
        active_assignments = queryset.filter(is_active=True).count()
        
        # 역할별 할당 수
        role_stats = queryset.filter(is_active=True).values(
            'volunteer_role__name', 'volunteer_role__category'
        ).annotate(count=Count('id')).order_by('-count')
        
        # 월별 할당 추이
        from django.utils import timezone
        today = timezone.now().date()
        monthly_assignments = queryset.filter(
            assigned_date__year=today.year,
            is_active=True
        ).extra(
            select={'month': 'EXTRACT(month FROM assigned_date)'}
        ).values('month').annotate(count=Count('id')).order_by('month')

        return Response({
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'role_stats': list(role_stats),
            'monthly_assignments': list(monthly_assignments)
        })