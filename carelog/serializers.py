from rest_framework import serializers
from .models import CareLog
from members.serializers import MemberBasicSerializer


class CareLogSerializer(serializers.ModelSerializer):
    """생활소식/심방기록 시리얼라이저"""
    member_detail = MemberBasicSerializer(source='member', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CareLog
        fields = [
            'id', 'member', 'member_detail', 'type', 'content', 'date',
            'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CareLogListSerializer(serializers.ModelSerializer):
    """생활소식/심방기록 목록용 시리얼라이저"""
    member_name = serializers.CharField(source='member.name', read_only=True)
    member_code = serializers.CharField(source='member.member_code', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = CareLog
        fields = [
            'id', 'member_name', 'member_code', 'type', 'type_display',
            'content', 'date', 'created_at'
        ]


class CareLogCreateSerializer(serializers.ModelSerializer):
    """생활소식/심방기록 생성용 시리얼라이저"""
    member_id = serializers.IntegerField()
    
    class Meta:
        model = CareLog
        fields = ['member_id', 'type', 'content', 'date']
    
    def validate(self, attrs):
        """유효성 검사"""
        member_id = attrs.get('member_id')
        try:
            from members.models import Member
            member = Member.objects.get(id=member_id)
            attrs['member'] = member
        except Member.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 멤버입니다.")
        
        return attrs
