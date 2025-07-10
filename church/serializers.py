from rest_framework import serializers
from .models import Church


class ChurchSerializer(serializers.ModelSerializer):
    """교회 정보 시리얼라이저"""
    member_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    local_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Church
        fields = (
            'id', 'name', 'code', 'address', 'phone', 'email', 'website',
            'pastor_name', 'pastor_phone', 'timezone', 'founding_date',
            'denomination', 'domain', 'is_active', 'max_members',
            'settings', 'logo', 'created_at', 'updated_at',
            'member_count', 'is_full', 'local_time'
        )
        read_only_fields = ('created_at', 'updated_at', 'member_count', 'is_full')
    
    def get_local_time(self, obj):
        """교회 현지 시간 반환"""
        return obj.get_local_time().isoformat()


class ChurchListSerializer(serializers.ModelSerializer):
    """교회 목록용 간단한 시리얼라이저"""
    member_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Church
        fields = (
            'id', 'name', 'code', 'address', 'phone', 'pastor_name',
            'is_active', 'member_count', 'created_at'
        )


class ChurchCreateSerializer(serializers.ModelSerializer):
    """교회 생성용 시리얼라이저"""
    
    class Meta:
        model = Church
        fields = (
            'name', 'code', 'address', 'phone', 'email', 'website',
            'pastor_name', 'pastor_phone', 'timezone', 'founding_date',
            'denomination', 'max_members', 'settings'
        )
    
    def validate_code(self, value):
        """교회 코드 유효성 검사"""
        if value and Church.objects.filter(code=value).exists():
            raise serializers.ValidationError("이미 사용 중인 교회 코드입니다.")
        return value


class ChurchSettingsSerializer(serializers.ModelSerializer):
    """교회 설정만 관리하는 시리얼라이저"""
    
    class Meta:
        model = Church
        fields = ('settings',)
    
    def validate_settings(self, value):
        """설정 값 유효성 검사"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("설정은 JSON 객체 형태여야 합니다.")
        return value
