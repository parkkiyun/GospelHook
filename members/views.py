from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from datetime import date, timedelta
from .models import Member, FamilyRelationship, FamilyTree
from .serializers import (
    MemberSerializer, MemberListSerializer, MemberCreateSerializer,
    MemberDetailSerializer, MemberBirthdaySerializer, MemberFamilyTreeSerializer,
    FamilyRelationshipSerializer, FamilyRelationshipCreateSerializer,
    FamilyRelationshipListSerializer, FamilyTreeSerializer, FamilyTreeCreateSerializer
)
from church_core.roles import SystemRole, Permission
from users.models import ChurchUser


class MemberViewSet(viewsets.ModelViewSet):
    """교인 관리 API ViewSet"""
    queryset = Member.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'gender', 'position', 'is_active', 'household']
    search_fields = ['name', 'member_code', 'phone', 'email', 'address']
    ordering_fields = ['name', 'member_code', 'birth_date', 'registration_date']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MemberListSerializer
        elif self.action == 'create':
            return MemberCreateSerializer
        elif self.action == 'retrieve':
            return MemberDetailSerializer
        elif self.action == 'birthdays':
            return MemberBirthdaySerializer
        elif self.action == 'family_tree':
            return MemberFamilyTreeSerializer
        return MemberSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        
        # 사용자가 속한 교회의 교인만 조회
        user_churches = user.church_users.values_list('church', flat=True)
        return self.queryset.filter(church__in=user_churches)
    
    def perform_create(self, serializer):
        """교인 생성 시 추가 처리"""
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
        """교인 생성"""
        if not self.check_permission(Permission.MEMBER_CREATE):
            return Response(
                {"detail": "교인 생성 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """교인 정보 수정"""
        if not self.check_permission(Permission.MEMBER_UPDATE):
            return Response(
                {"detail": "교인 수정 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """교인 삭제"""
        if not self.check_permission(Permission.MEMBER_DELETE):
            return Response(
                {"detail": "교인 삭제 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def set_household(self, request, pk=None):
        """세대주 설정"""
        member = self.get_object()
        household_id = request.data.get('household_id')
        
        if household_id:
            try:
                household = Member.objects.get(id=household_id, church=member.church)
                member.household = household
                member.save()
                return Response({
                    'message': '세대주가 설정되었습니다.',
                    'household': household.name
                })
            except Member.DoesNotExist:
                return Response(
                    {"detail": "유효하지 않은 세대주입니다."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            member.household = None
            member.save()
            return Response({'message': '세대주 설정이 해제되었습니다.'})
    
    @action(detail=False, methods=['get'])
    def birthdays(self, request):
        """생일자 목록 조회"""
        # 기간 파라미터
        days = int(request.query_params.get('days', 30))
        today = date.today()
        
        # 생일이 다가오는 교인 찾기
        members = self.get_queryset().filter(
            birth_date__isnull=False,
            is_active=True,
            status='active'
        )
        
        birthday_members = []
        for member in members:
            days_until = member.days_until_birthday()
            if days_until is not None and 0 <= days_until <= days:
                birthday_members.append(member)
        
        # 생일까지 남은 일수로 정렬
        birthday_members.sort(key=lambda x: x.days_until_birthday())
        
        serializer = self.get_serializer(birthday_members, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """교인 통계"""
        queryset = self.get_queryset()
        
        # 기본 통계
        total = queryset.count()
        active = queryset.filter(status='active').count()
        
        # 성별 통계
        male = queryset.filter(gender='M').count()
        female = queryset.filter(gender='F').count()
        
        # 연령대 통계
        age_groups = {
            '영유아부': 0,
            '유년부': 0,
            '중등부': 0,
            '고등부': 0,
            '청년부': 0,
            '장년부': 0,
            '노년부': 0,
            '연령미상': 0
        }
        
        for member in queryset:
            age_group = member.age_group
            if age_group:
                age_groups[age_group] += 1
            else:
                age_groups['연령미상'] += 1
        
        # 직분 통계
        position_stats = {}
        for member in queryset.exclude(position=''):
            position = member.position or '일반'
            position_stats[position] = position_stats.get(position, 0) + 1
        
        return Response({
            'total': total,
            'active': active,
            'inactive': total - active,
            'gender': {
                'male': male,
                'female': female,
                'unknown': total - male - female
            },
            'age_groups': age_groups,
            'positions': position_stats
        })
    
    @action(detail=False, methods=['get'])
    def search_duplicate(self, request):
        """중복 교인 검색"""
        name = request.query_params.get('name', '')
        phone = request.query_params.get('phone', '')
        
        if not name and not phone:
            return Response(
                {"detail": "이름 또는 전화번호를 입력해주세요."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset()
        
        # 이름과 전화번호로 검색
        conditions = Q()
        if name:
            conditions |= Q(name=name)
        if phone:
            conditions |= Q(phone=phone)
        
        duplicates = queryset.filter(conditions)
        serializer = MemberListSerializer(duplicates, many=True)
        
        return Response({
            'count': duplicates.count(),
            'members': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def family_tree(self, request, pk=None):
        """교인의 가족 관계도 조회"""
        member = self.get_object()
        serializer = MemberFamilyTreeSerializer(member)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_family_relationship(self, request, pk=None):
        """가족 관계 추가"""
        if not self.check_permission(Permission.MEMBER_UPDATE):
            return Response(
                {"detail": "가족 관계 설정 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        member = self.get_object()
        data = request.data.copy()
        data['from_member_id'] = member.id
        
        serializer = FamilyRelationshipCreateSerializer(data=data)
        if serializer.is_valid():
            relationship = serializer.save(created_by=request.user)
            return Response({
                'message': '가족 관계가 추가되었습니다.',
                'relationship': FamilyRelationshipSerializer(relationship).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def family_relationships(self, request, pk=None):
        """교인의 가족 관계 목록"""
        member = self.get_object()
        relationships = member.get_family_relationships()
        serializer = FamilyRelationshipListSerializer(relationships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def family_summary(self, request, pk=None):
        """교인의 가족 관계 요약"""
        member = self.get_object()
        
        summary = {
            'member': MemberListSerializer(member).data,
            'spouse': None,
            'children': [],
            'parents': [],
            'siblings': [],
            'total_relationships': member.get_family_relationships().count()
        }
        
        spouse = member.get_spouse()
        if spouse:
            summary['spouse'] = MemberListSerializer(spouse).data
        
        summary['children'] = MemberListSerializer(member.get_children(), many=True).data
        summary['parents'] = MemberListSerializer(member.get_parents(), many=True).data
        summary['siblings'] = MemberListSerializer(member.get_siblings(), many=True).data
        
        return Response(summary)


class FamilyRelationshipViewSet(viewsets.ModelViewSet):
    """가족 관계 관리 ViewSet"""
    queryset = FamilyRelationship.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['relationship', 'is_confirmed']
    search_fields = ['from_member__name', 'to_member__name', 'relationship_detail']
    ordering = ['from_member__name', 'relationship']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FamilyRelationshipListSerializer
        elif self.action == 'create':
            return FamilyRelationshipCreateSerializer
        return FamilyRelationshipSerializer
    
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
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """가족 관계 통계"""
        queryset = self.get_queryset()
        
        # 관계 유형별 통계
        relationship_stats = {}
        for relationship_type in FamilyRelationship.RelationshipType.values:
            count = queryset.filter(relationship=relationship_type).count()
            if count > 0:
                relationship_stats[relationship_type] = count
        
        # 확인된 관계 통계
        confirmed_count = queryset.filter(is_confirmed=True).count()
        unconfirmed_count = queryset.filter(is_confirmed=False).count()
        
        return Response({
            'total_relationships': queryset.count(),
            'confirmed_relationships': confirmed_count,
            'unconfirmed_relationships': unconfirmed_count,
            'relationship_types': relationship_stats
        })


class FamilyTreeViewSet(viewsets.ModelViewSet):
    """가족 계보 관리 ViewSet"""
    queryset = FamilyTree.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['family_name', 'description', 'root_member__name']
    ordering = ['family_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FamilyTreeCreateSerializer
        return FamilyTreeSerializer
    
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
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """가족 계보에 구성원 추가"""
        family_tree = self.get_object()
        member_id = request.data.get('member_id')
        
        try:
            member = Member.objects.get(id=member_id, church=family_tree.church)
            family_tree.family_members.add(member)
            return Response({
                'message': f'{member.name} 교인이 {family_tree.family_name}에 추가되었습니다.'
            })
        except Member.DoesNotExist:
            return Response(
                {"detail": "유효하지 않은 교인입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """가족 계보에서 구성원 제거"""
        family_tree = self.get_object()
        member_id = request.data.get('member_id')
        
        try:
            member = Member.objects.get(id=member_id, church=family_tree.church)
            family_tree.family_members.remove(member)
            return Response({
                'message': f'{member.name} 교인이 {family_tree.family_name}에서 제거되었습니다.'
            })
        except Member.DoesNotExist:
            return Response(
                {"detail": "유효하지 않은 교인입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def family_relationships(self, request, pk=None):
        """가족 계보 내 모든 관계 조회"""
        family_tree = self.get_object()
        relationships = family_tree.get_family_relationships()
        serializer = FamilyRelationshipListSerializer(relationships, many=True)
        return Response(serializer.data)
