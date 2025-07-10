from rest_framework import serializers
from .models import WorshipRecord
from members.serializers import MemberListSerializer


class WorshipRecordListSerializer(serializers.ModelSerializer):
    """예배 기록 목록용 Serializer"""
    worship_type_display = serializers.CharField(source='get_worship_type_display', read_only=True)
    attendee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WorshipRecord
        fields = [
            'id', 'date', 'worship_type', 'worship_type_display',
            'preacher', 'theme', 'attendee_count', 'created_at'
        ]
    
    def get_attendee_count(self, obj):
        """참석자 수 반환"""
        return obj.attendees.count()


class WorshipRecordDetailSerializer(serializers.ModelSerializer):
    """예배 기록 상세용 Serializer"""
    worship_type_display = serializers.CharField(source='get_worship_type_display', read_only=True)
    attendees_detail = MemberListSerializer(source='attendees', many=True, read_only=True)
    attendee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WorshipRecord
        fields = [
            'id', 'church', 'date', 'worship_type', 'worship_type_display',
            'preacher', 'theme', 'scripture', 'attendees', 'attendees_detail',
            'attendee_count', 'summary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['church', 'created_at', 'updated_at']
    
    def get_attendee_count(self, obj):
        """참석자 수 반환"""
        return obj.attendees.count()


class WorshipRecordCreateSerializer(serializers.ModelSerializer):
    """예배 기록 생성용 Serializer"""
    
    class Meta:
        model = WorshipRecord
        fields = [
            'date', 'worship_type', 'preacher', 'theme', 
            'scripture', 'attendees', 'summary'
        ]
    
    def validate_date(self, value):
        """날짜 유효성 검사"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("미래 날짜는 입력할 수 없습니다.")
        return value
    
    def validate_preacher(self, value):
        """설교자 이름 유효성 검사"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("설교자 이름은 2자 이상이어야 합니다.")
        return value.strip()
