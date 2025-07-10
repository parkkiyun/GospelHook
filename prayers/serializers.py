from rest_framework import serializers
from .models import Prayer, PrayerComment, PrayerGroup, PrayerGroupMember
from members.serializers import MemberBasicSerializer
from groups.serializers import GroupListSerializer


class PrayerCommentSerializer(serializers.ModelSerializer):
    """기도제목 댓글 시리얼라이저"""
    member = MemberBasicSerializer(read_only=True)
    member_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PrayerComment
        fields = [
            'id', 'member', 'member_id', 'content', 'is_encouragement',
            'is_private', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PrayerListSerializer(serializers.ModelSerializer):
    """기도제목 목록용 시리얼라이저"""
    member_name = serializers.CharField(source='member.name', read_only=True)
    member_code = serializers.CharField(source='member.member_code', read_only=True)
    days_to_target = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    prayer_duration = serializers.IntegerField(read_only=True)
    tags_list = serializers.ListField(source='get_tags_list', read_only=True)
    
    class Meta:
        model = Prayer
        fields = [
            'id', 'title', 'member_name', 'member_code', 'prayer_type',
            'priority', 'status', 'is_public', 'prayer_date', 'target_date',
            'answered_date', 'days_to_target', 'is_overdue', 'prayer_duration',
            'prayer_count', 'tags_list', 'created_at'
        ]


class PrayerCreateSerializer(serializers.ModelSerializer):
    """기도제목 생성용 시리얼라이저"""
    member_id = serializers.IntegerField()
    group_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = Prayer
        fields = [
            'member_id', 'title', 'content', 'prayer_type', 'priority',
            'status', 'is_public', 'is_shared_with_leaders', 'prayer_date',
            'target_date', 'group_id', 'tags', 'private_note'
        ]
    
    def validate(self, attrs):
        """유효성 검사"""
        # 멤버 존재 확인
        member_id = attrs.get('member_id')
        try:
            from members.models import Member
            member = Member.objects.get(id=member_id)
            attrs['member'] = member
        except Member.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 멤버입니다.")
        
        # 그룹 존재 확인 (선택적)
        group_id = attrs.get('group_id')
        if group_id:
            try:
                from groups.models import Group
                group = Group.objects.get(id=group_id)
                attrs['group'] = group
            except Group.DoesNotExist:
                raise serializers.ValidationError("존재하지 않는 그룹입니다.")
        
        return attrs


class PrayerDetailSerializer(serializers.ModelSerializer):
    """기도제목 상세 정보용 시리얼라이저"""
    member = MemberBasicSerializer(read_only=True)
    group = GroupListSerializer(read_only=True)
    comments = PrayerCommentSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    days_to_target = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    prayer_duration = serializers.IntegerField(read_only=True)
    tags_list = serializers.ListField(source='get_tags_list', read_only=True)
    
    class Meta:
        model = Prayer
        fields = [
            'id', 'member', 'title', 'content', 'prayer_type', 'priority',
            'status', 'is_public', 'is_shared_with_leaders', 'prayer_date',
            'target_date', 'answered_date', 'group', 'tags', 'tags_list',
            'answer_note', 'private_note', 'prayer_count', 'days_to_target',
            'is_overdue', 'prayer_duration', 'comments', 'created_by_name',
            'created_at', 'updated_at'
        ]


class PrayerSerializer(serializers.ModelSerializer):
    """기본 기도제목 시리얼라이저"""
    member = MemberBasicSerializer(read_only=True)
    group = GroupListSerializer(read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    days_to_target = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    prayer_duration = serializers.IntegerField(read_only=True)
    tags_list = serializers.ListField(source='get_tags_list', read_only=True)
    
    class Meta:
        model = Prayer
        fields = [
            'id', 'member', 'title', 'content', 'prayer_type', 'priority',
            'status', 'is_public', 'is_shared_with_leaders', 'prayer_date',
            'target_date', 'answered_date', 'group', 'tags', 'tags_list',
            'answer_note', 'prayer_count', 'days_to_target', 'is_overdue',
            'prayer_duration', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'prayer_count', 'created_at', 'updated_at']


class PrayerStatsSerializer(serializers.Serializer):
    """기도제목 통계용 시리얼라이저"""
    total_prayers = serializers.IntegerField()
    active_prayers = serializers.IntegerField()
    answered_prayers = serializers.IntegerField()
    overdue_prayers = serializers.IntegerField()
    prayer_types = serializers.DictField()
    priority_stats = serializers.DictField()
    recent_prayers = serializers.ListField()


class PrayerGroupMemberSerializer(serializers.ModelSerializer):
    """기도 그룹 멤버 시리얼라이저"""
    member = MemberBasicSerializer(read_only=True)
    member_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PrayerGroupMember
        fields = [
            'id', 'member', 'member_id', 'role', 'joined_date', 'is_active'
        ]
        read_only_fields = ['id']


class PrayerGroupSerializer(serializers.ModelSerializer):
    """기도 그룹 시리얼라이저"""
    group_members = PrayerGroupMemberSerializer(many=True, read_only=True)
    member_count = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = PrayerGroup
        fields = [
            'id', 'name', 'description', 'is_public', 'is_active',
            'meeting_day', 'meeting_time', 'member_count', 'group_members',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PrayerGroupListSerializer(serializers.ModelSerializer):
    """기도 그룹 목록용 시리얼라이저"""
    member_count = serializers.ReadOnlyField()
    
    class Meta:
        model = PrayerGroup
        fields = [
            'id', 'name', 'description', 'is_public', 'is_active',
            'meeting_day', 'meeting_time', 'member_count'
        ]