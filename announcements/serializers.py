from rest_framework import serializers
from .models import Announcement, PushLog
from users.serializers import UserSerializer


class AnnouncementListSerializer(serializers.ModelSerializer):
    """공지사항 목록용 Serializer"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    content_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content_preview', 'created_by_name',
            'push_enabled', 'created_at'
        ]
    
    def get_content_preview(self, obj):
        """내용 미리보기 (100자 제한)"""
        if len(obj.content) > 100:
            return f"{obj.content[:100]}..."
        return obj.content


class AnnouncementDetailSerializer(serializers.ModelSerializer):
    """공지사항 상세용 Serializer"""
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    push_log_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'church', 'title', 'content', 'visible_roles',
            'created_by', 'created_by_detail', 'push_enabled',
            'push_log_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['church', 'created_by', 'created_at', 'updated_at']
    
    def get_push_log_count(self, obj):
        """푸시 알림 발송 수 반환"""
        return obj.pushlog_set.filter(status='SENT').count()


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    """공지사항 생성용 Serializer"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'visible_roles', 'push_enabled']
    
    def validate_title(self, value):
        """제목 유효성 검사"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("제목은 2자 이상이어야 합니다.")
        return value.strip()
    
    def validate_content(self, value):
        """내용 유효성 검사"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("내용은 5자 이상이어야 합니다.")
        return value.strip()
    
    def validate_visible_roles(self, value):
        """가시 직책 유효성 검사"""
        if value:
            valid_roles = ['SUPER_ADMIN', 'CHURCH_ADMIN', 'CHURCH_STAFF', 'MEMBER']
            for role in value:
                if role not in valid_roles:
                    raise serializers.ValidationError(
                        f"유효하지 않은 직책입니다: {role}. "
                        f"유효한 직책: {', '.join(valid_roles)}"
                    )
        return value


class PushLogSerializer(serializers.ModelSerializer):
    """푸시 알림 로그 Serializer"""
    announcement_title = serializers.CharField(source='announcement.title', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PushLog
        fields = [
            'id', 'announcement', 'announcement_title', 'user',
            'user_name', 'sent_at', 'status', 'status_display'
        ]
        read_only_fields = ['sent_at']