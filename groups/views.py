from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import Group, GroupMember
from .serializers import (
    GroupSerializer, GroupListSerializer, GroupCreateSerializer,
    GroupDetailSerializer, GroupStatsSerializer, GroupMemberSerializer
)
from church_core.roles import SystemRole, Permission
from users.models import ChurchUser


class GroupViewSet(viewsets.ModelViewSet):
    """그룹 관리 API ViewSet"""
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group_type', 'management_type', 'is_active', 'parent_group']
    search_fields = ['name', 'code', 'description', 'leader__name']
    ordering_fields = ['name', 'order', 'created_at', 'member_count']
    ordering = ['order', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return GroupListSerializer
        elif self.action == 'create':
            return GroupCreateSerializer
        elif self.action == 'retrieve':
            return GroupDetailSerializer
        elif self.action == 'statistics':
            return GroupStatsSerializer
        elif self.action in ['add_member', 'remove_member', 'update_member']:
            return GroupMemberSerializer
        return GroupSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        
        # 사용자가 속한 교회의 그룹만 조회
        user_churches = user.church_users.values_list('church', flat=True)
        return self.queryset.filter(church__in=user_churches)
    
    def perform_create(self, serializer):
        """그룹 생성 시 추가 처리"""
        # 교회 정보 자동 설정
        church_user = self.request.user.church_users.first()
        if church_user:
            serializer.save(church=church_user.church, created_by=self.request.user)
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
        """그룹 생성"""
        if not self.check_permission(Permission.GROUP_CREATE):
            return Response(
                {"detail": "그룹 생성 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """그룹 수정"""
        if not self.check_permission(Permission.GROUP_UPDATE):
            return Response(
                {"detail": "그룹 수정 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """그룹 삭제"""
        if not self.check_permission(Permission.GROUP_DELETE):
            return Response(
                {"detail": "그룹 삭제 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """그룹에 멤버 추가"""
        group = self.get_object()
        member_id = request.data.get('member_id')
        role = request.data.get('role', 'member')
        
        if not member_id:
            return Response(
                {"detail": "멤버 ID가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from members.models import Member
            member = Member.objects.get(id=member_id, church=group.church)
        except Member.DoesNotExist:
            return Response(
                {"detail": "유효하지 않은 멤버입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 그룹 가입 가능 여부 확인
        can_add, error_message = group.can_add_member(member)
        if not can_add:
            return Response(
                {"detail": error_message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 이미 가입된 멤버인지 확인
        if GroupMember.objects.filter(group=group, member=member).exists():
            return Response(
                {"detail": "이미 그룹에 가입된 멤버입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 그룹 멤버 추가
        group_member = GroupMember.objects.create(
            group=group,
            member=member,
            role=role
        )
        
        serializer = GroupMemberSerializer(group_member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """그룹에서 멤버 제거"""
        group = self.get_object()
        member_id = request.data.get('member_id')
        
        if not member_id:
            return Response(
                {"detail": "멤버 ID가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            group_member = GroupMember.objects.get(
                group=group,
                member_id=member_id
            )
            group_member.delete()
            return Response({"message": "멤버가 그룹에서 제거되었습니다."})
        except GroupMember.DoesNotExist:
            return Response(
                {"detail": "그룹에 속하지 않은 멤버입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'])
    def update_member(self, request, pk=None):
        """그룹 멤버 정보 수정"""
        group = self.get_object()
        member_id = request.data.get('member_id')
        
        if not member_id:
            return Response(
                {"detail": "멤버 ID가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            group_member = GroupMember.objects.get(
                group=group,
                member_id=member_id
            )
            
            serializer = GroupMemberSerializer(
                group_member, 
                data=request.data, 
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except GroupMember.DoesNotExist:
            return Response(
                {"detail": "그룹에 속하지 않은 멤버입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def hierarchy(self, request):
        """그룹 계층 구조 조회"""
        queryset = self.get_queryset().filter(is_active=True)
        root_groups = queryset.filter(parent_group=None)
        
        def build_hierarchy(groups):
            result = []
            for group in groups:
                group_data = GroupListSerializer(group).data
                sub_groups = queryset.filter(parent_group=group)
                if sub_groups.exists():
                    group_data['children'] = build_hierarchy(sub_groups)
                result.append(group_data)
            return result
        
        hierarchy = build_hierarchy(root_groups)
        return Response(hierarchy)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """그룹 통계"""
        queryset = self.get_queryset()
        
        # 기본 통계
        total_groups = queryset.count()
        active_groups = queryset.filter(is_active=True).count()
        
        # 그룹 유형별 통계
        group_types = {}
        for group_type in Group.GroupType.values:
            group_types[group_type] = queryset.filter(group_type=group_type).count()
        
        # 멤버 관련 통계
        total_members = GroupMember.objects.filter(
            group__in=queryset,
            is_active=True
        ).count()
        
        avg_members_per_group = total_members / active_groups if active_groups > 0 else 0
        
        # 정원 초과 그룹 수
        full_groups = sum(1 for group in queryset if group.is_full)
        
        return Response({
            'total_groups': total_groups,
            'active_groups': active_groups,
            'group_types': group_types,
            'total_members': total_members,
            'avg_members_per_group': round(avg_members_per_group, 2),
            'full_groups': full_groups
        })
    
    @action(detail=False, methods=['post'])
    def auto_assign_members(self, request):
        """자동 멤버 배정"""
        if not self.check_permission(Permission.GROUP_UPDATE):
            return Response(
                {"detail": "그룹 관리 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        auto_groups = self.get_queryset().filter(
            management_type__in=['auto', 'hybrid'],
            is_active=True
        )
        
        assigned_count = 0
        errors = []
        
        for group in auto_groups:
            try:
                from members.models import Member
                # 나이 조건에 맞는 멤버 찾기
                eligible_members = Member.objects.filter(
                    church=group.church,
                    is_active=True,
                    status='active'
                ).exclude(
                    group_memberships__group=group
                )
                
                for member in eligible_members:
                    if member.age and group.age_min <= member.age <= group.age_max:
                        can_add, _ = group.can_add_member(member)
                        if can_add:
                            GroupMember.objects.create(
                                group=group,
                                member=member,
                                role='member'
                            )
                            assigned_count += 1
                        
            except Exception as e:
                errors.append(f"그룹 {group.name}: {str(e)}")
        
        return Response({
            'message': f'{assigned_count}명이 자동으로 배정되었습니다.',
            'assigned_count': assigned_count,
            'errors': errors
        })