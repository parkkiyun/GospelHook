from rest_framework import serializers
from .models import Bulletin


class BulletinListSerializer(serializers.ModelSerializer):
    """주보 목록용 Serializer"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Bulletin
        fields = [
            'id', 'title', 'date', 'file_url', 'created_at'
        ]
    
    def get_file_url(self, obj):
        """파일 URL 반환"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class BulletinDetailSerializer(serializers.ModelSerializer):
    """주보 상세용 Serializer"""
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = Bulletin
        fields = [
            'id', 'church', 'title', 'file', 'file_url', 'file_size',
            'date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['church', 'created_at', 'updated_at']
    
    def get_file_url(self, obj):
        """파일 URL 반환"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size(self, obj):
        """파일 크기 반환 (bytes)"""
        if obj.file:
            try:
                return obj.file.size
            except:
                return None
        return None


class BulletinCreateSerializer(serializers.ModelSerializer):
    """주보 생성용 Serializer"""
    
    class Meta:
        model = Bulletin
        fields = ['title', 'file', 'date']
        
    def validate_file(self, value):
        """파일 유효성 검사"""
        if value:
            # 파일 크기 체크 (10MB 제한)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("파일 크기는 10MB를 초과할 수 없습니다.")
            
            # 파일 확장자 체크
            allowed_extensions = ['.pdf', '.doc', '.docx']
            import os
            file_extension = os.path.splitext(value.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError(
                    f"허용되지 않는 파일 형식입니다. 허용 형식: {', '.join(allowed_extensions)}"
                )
        
        return value
