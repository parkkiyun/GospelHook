from rest_framework import serializers
from .models import Group, GroupMember
from members.serializers import MemberBasicSerializer


class GroupMemberSerializer(serializers.ModelSerializer):
    member = MemberBasicSerializer(read_only=True)
    member_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = GroupMember
        fields = ['id', 'member', 'member_id', 'role', 'joined_date', 'is_active', 'notes']
        read_only_fields = ['id']


class GroupListSerializer(serializers.ModelSerializer):
    """그룹 목록용 시리얼라이저"""
    member_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    parent_group_name = serializers.CharField(source='parent_group.name', read_only=True)
    leader_name = serializers.CharField(source='leader.name', read_only=True)
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'code', 'group_type', 'management_type',
            'parent_group_name', 'leader_name', 'member_count', 'is_full',
            'is_active', 'meeting_day', 'meeting_time', 'meeting_place',
            'created_at'
        ]


class GroupCreateSerializer(serializers.ModelSerializer):
    """그룹 생성용 시리얼라이저"""
    
    class Meta:
        model = Group
        fields = [
            'name', 'code', 'description', 'group_type', 'parent_group',
            'management_type', 'age_min', 'age_max', 'leader',
            'meeting_day', 'meeting_time', 'meeting_place', 'max_members'
        ]
        
    def validate(self, attrs):
        if attrs.get('management_type') in ['auto', 'hybrid']:
            if not attrs.get('age_min') or not attrs.get('age_max'):
                raise serializers.ValidationError(
                    "자동 관리 그룹은 나이 범위를 설정해야 합니다."
                )
            if attrs.get('age_min') > attrs.get('age_max'):
                raise serializers.ValidationError(
                    "최소 나이는 최대 나이보다 작아야 합니다."
                )
        return attrs


class GroupDetailSerializer(serializers.ModelSerializer):
    """그룹 상세 정보용 시리얼라이저"""
    member_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    parent_group_name = serializers.CharField(source='parent_group.name', read_only=True)
    leader_name = serializers.CharField(source='leader.name', read_only=True)
    hierarchy_name = serializers.CharField(source='get_hierarchy_name', read_only=True)
    group_members = GroupMemberSerializer(many=True, read_only=True)
    sub_groups = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'code', 'description', 'group_type', 'management_type',
            'parent_group', 'parent_group_name', 'leader', 'leader_name',
            'age_min', 'age_max', 'member_count', 'is_full', 'max_members',
            'meeting_day', 'meeting_time', 'meeting_place', 'is_active',
            'order', 'hierarchy_name', 'group_members', 'sub_groups',
            'created_at', 'updated_at'
        ]
        
    def get_sub_groups(self, obj):
        sub_groups = obj.sub_groups.filter(is_active=True)
        return GroupListSerializer(sub_groups, many=True).data


class GroupSerializer(serializers.ModelSerializer):
    """기본 그룹 시리얼라이저"""
    member_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    parent_group_name = serializers.CharField(source='parent_group.name', read_only=True)
    leader_name = serializers.CharField(source='leader.name', read_only=True)
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'code', 'description', 'group_type', 'management_type',
            'parent_group', 'parent_group_name', 'leader', 'leader_name',
            'age_min', 'age_max', 'member_count', 'is_full', 'max_members',
            'meeting_day', 'meeting_time', 'meeting_place', 'is_active',
            'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GroupStatsSerializer(serializers.Serializer):
    """그룹 통계용 시리얼라이저"""
    total_groups = serializers.IntegerField()
    active_groups = serializers.IntegerField()
    group_types = serializers.DictField()
    total_members = serializers.IntegerField()
    avg_members_per_group = serializers.FloatField()
    full_groups = serializers.IntegerField()
