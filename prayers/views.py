from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import Prayer, PrayerComment, PrayerGroup, PrayerGroupMember
from .serializers import (
    PrayerSerializer, PrayerListSerializer, PrayerCreateSerializer,
    PrayerDetailSerializer, PrayerStatsSerializer, PrayerCommentSerializer,
    PrayerGroupSerializer, PrayerGroupListSerializer, PrayerGroupMemberSerializer
)
from church_core.roles import SystemRole, Permission
from users.models import ChurchUser


class PrayerViewSet(viewsets.ModelViewSet):
    """기도제목 관리 API ViewSet"""
    queryset = Prayer.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['prayer_type', 'priority', 'status', 'is_public', 'group']
    search_fields = ['title', 'content', 'member__name', 'tags']
    ordering_fields = ['prayer_date', 'target_date', 'priority', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PrayerListSerializer
        elif self.action == 'create':
            return PrayerCreateSerializer
        elif self.action == 'retrieve':
            return PrayerDetailSerializer
        elif self.action == 'statistics':
            return PrayerStatsSerializer
        elif self.action in ['add_comment', 'update_comment']:
            return PrayerCommentSerializer
        return PrayerSerializer
    
    def get_queryset(self):
        user = self.request.user
        church_id = self.kwargs.get('church_id')
        
        if user.is_superuser:
            queryset = self.queryset
        else:
            # 사용자가 속한 교회의 기도제목만 조회
            user_churches = user.church_users.values_list('church', flat=True)
            queryset = self.queryset.filter(church__in=user_churches)
        
        # church_id가 있으면 해당 교회로 필터링
        if church_id:
            queryset = queryset.filter(church_id=church_id)
        
        # 권한에 따른 필터링
        if not user.is_superuser:
            church_user = user.church_users.filter(church_id=church_id).first()
            if church_user and church_user.role == SystemRole.MEMBER:
                # 일반 교인은 공개 기도제목과 자신의 기도제목만 조회
                queryset = queryset.filter(
                    Q(is_public=True) | Q(member__user=user)
                )
        
        return queryset
    
    def perform_create(self, serializer):
        """기도제목 생성 시 추가 처리"""
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
        """기도제목 생성"""
        if not self.check_permission(Permission.PRAYER_CREATE):
            return Response(
                {"detail": "기도제목 생성 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """기도제목 수정"""
        prayer = self.get_object()
        
        # 본인의 기도제목이거나 권한이 있는 경우만 수정 가능
        if prayer.member.user != request.user and not self.check_permission(Permission.PRAYER_UPDATE):
            return Response(
                {"detail": "기도제목 수정 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """기도제목 삭제"""
        prayer = self.get_object()
        
        # 본인의 기도제목이거나 권한이 있는 경우만 삭제 가능
        if prayer.member.user != request.user and not self.check_permission(Permission.PRAYER_DELETE):
            return Response(
                {"detail": "기도제목 삭제 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def pray(self, request, pk=None):
        """기도 카운트 증가"""
        prayer = self.get_object()
        prayer.increment_prayer_count()
        
        return Response({
            'message': '기도해주셔서 감사합니다.',
            'prayer_count': prayer.prayer_count
        })
    
    @action(detail=True, methods=['post'])
    def mark_answered(self, request, pk=None):
        """기도 응답 처리"""
        prayer = self.get_object()
        
        # 본인의 기도제목이거나 권한이 있는 경우만 가능
        if prayer.member.user != request.user and not self.check_permission(Permission.PRAYER_UPDATE):
            return Response(
                {"detail": "기도제목 수정 권한이 없습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        prayer.status = Prayer.Status.ANSWERED
        prayer.answer_note = request.data.get('answer_note', '')
        prayer.save()
        
        return Response({
            'message': '기도제목이 응답됨으로 처리되었습니다.',
            'answered_date': prayer.answered_date
        })
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """댓글 추가"""
        prayer = self.get_object()
        member_id = request.data.get('member_id')
        
        try:
            from members.models import Member
            church_id = self.kwargs.get('church_id')
            member = Member.objects.get(id=member_id, church_id=church_id)
        except Member.DoesNotExist:
            return Response(
                {"detail": "유효하지 않은 멤버입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PrayerCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(prayer=prayer, member=member)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """기도제목 통계"""
        queryset = self.get_queryset()
        
        # 기본 통계
        total_prayers = queryset.count()
        active_prayers = queryset.filter(status=Prayer.Status.ACTIVE).count()
        answered_prayers = queryset.filter(status=Prayer.Status.ANSWERED).count()
        overdue_prayers = queryset.filter(
            status=Prayer.Status.ACTIVE,
            target_date__lt=date.today()
        ).count()
        
        # 기도제목 유형별 통계
        prayer_types = {}
        for prayer_type in Prayer.PrayerType.values:
            count = queryset.filter(prayer_type=prayer_type).count()
            if count > 0:
                prayer_types[prayer_type] = count
        
        # 우선순위별 통계
        priority_stats = {}
        for priority in Prayer.Priority.values:
            count = queryset.filter(priority=priority).count()
            if count > 0:
                priority_stats[priority] = count
        
        # 최근 기도제목
        recent_prayers = PrayerListSerializer(
            queryset.order_by('-created_at')[:5], 
            many=True
        ).data
        
        return Response({
            'total_prayers': total_prayers,
            'active_prayers': active_prayers,
            'answered_prayers': answered_prayers,
            'overdue_prayers': overdue_prayers,
            'prayer_types': prayer_types,
            'priority_stats': priority_stats,
            'recent_prayers': recent_prayers
        })
    
    @action(detail=False, methods=['get'])
    def my_prayers(self, request):
        """내 기도제목 조회"""
        user = request.user
        church_id = self.kwargs.get('church_id')
        
        try:
            from members.models import Member
            member = Member.objects.get(user=user, church_id=church_id)
            prayers = self.get_queryset().filter(member=member)
            
            page = self.paginate_queryset(prayers)
            if page is not None:
                serializer = PrayerListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = PrayerListSerializer(prayers, many=True)
            return Response(serializer.data)
            
        except Member.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """긴급 기도제목 조회"""
        urgent_prayers = self.get_queryset().filter(
            priority=Prayer.Priority.URGENT,
            status=Prayer.Status.ACTIVE
        ).order_by('-created_at')
        
        serializer = PrayerListSerializer(urgent_prayers, many=True)
        return Response(serializer.data)


class PrayerGroupViewSet(viewsets.ModelViewSet):
    """기도 그룹 관리 API ViewSet"""
    queryset = PrayerGroup.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PrayerGroupListSerializer
        elif self.action in ['add_member', 'remove_member', 'update_member']:
            return PrayerGroupMemberSerializer
        return PrayerGroupSerializer
    
    def get_queryset(self):
        user = self.request.user
        church_id = self.kwargs.get('church_id')
        
        if user.is_superuser:
            queryset = self.queryset
        else:
            # 사용자가 속한 교회의 기도 그룹만 조회
            user_churches = user.church_users.values_list('church', flat=True)
            queryset = self.queryset.filter(church__in=user_churches)
        
        # church_id가 있으면 해당 교회로 필터링
        if church_id:
            queryset = queryset.filter(church_id=church_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """기도 그룹 생성 시 추가 처리"""
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
        """기도 그룹에 멤버 추가"""
        group = self.get_object()
        member_id = request.data.get('member_id')
        role = request.data.get('role', 'member')
        
        try:
            from members.models import Member
            church_id = self.kwargs.get('church_id')
            member = Member.objects.get(id=member_id, church_id=church_id)
        except Member.DoesNotExist:
            return Response(
                {"detail": "유효하지 않은 멤버입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 이미 가입된 멤버인지 확인
        if PrayerGroupMember.objects.filter(prayer_group=group, member=member).exists():
            return Response(
                {"detail": "이미 그룹에 가입된 멤버입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        group_member = PrayerGroupMember.objects.create(
            prayer_group=group,
            member=member,
            role=role
        )
        
        serializer = PrayerGroupMemberSerializer(group_member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """기도 그룹에서 멤버 제거"""
        group = self.get_object()
        member_id = request.data.get('member_id')
        
        try:
            group_member = PrayerGroupMember.objects.get(
                prayer_group=group,
                member_id=member_id
            )
            group_member.delete()
            return Response({"message": "멤버가 그룹에서 제거되었습니다."})
        except PrayerGroupMember.DoesNotExist:
            return Response(
                {"detail": "그룹에 속하지 않은 멤버입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )