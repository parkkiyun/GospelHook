from rest_framework import serializers
from .models import Offering
from members.serializers import MemberSerializer
from users.serializers import UserSerializer


class OfferingListSerializer(serializers.ModelSerializer):
    """헌금 목록용 Serializer"""
    member_name = serializers.CharField(source='member.name', read_only=True, default='익명')
    offering_type_display = serializers.CharField(source='get_offering_type_display', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)
    
    class Meta:
        model = Offering
        fields = [
            'id', 'member_name', 'amount', 'offering_type', 'offering_type_display',
            'date', 'recorded_by_name', 'created_at'
        ]
    
    def to_representation(self, instance):
        """민감한 정보 보호 처리"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # 관리자가 아닌 경우 헌금자 정보 숨김
        if request and not (request.user.is_superuser or self._is_admin(request)):
            data['member_name'] = '익명'
        
        return data
    
    def _is_admin(self, request):
        """관리자 여부 확인"""
        try:
            church_id = self.context.get('church_id')
            if church_id:
                church_user = request.user.church_users.get(church_id=church_id)
                return church_user.role in ['CHURCH_ADMIN', 'CHURCH_STAFF']
        except:
            pass
        return False


class OfferingDetailSerializer(serializers.ModelSerializer):
    """헌금 상세용 Serializer"""
    member_detail = MemberSerializer(source='member', read_only=True)
    recorded_by_detail = UserSerializer(source='recorded_by', read_only=True)
    offering_type_display = serializers.CharField(source='get_offering_type_display', read_only=True)
    
    class Meta:
        model = Offering
        fields = [
            'id', 'church', 'member', 'member_detail', 'amount', 'offering_type',
            'offering_type_display', 'date', 'recorded_by', 'recorded_by_detail',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['church', 'recorded_by', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """민감한 정보 보호 처리"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # 관리자가 아닌 경우 헌금자 정보 숨김
        if request and not (request.user.is_superuser or self._is_admin(request)):
            data['member'] = None
            data['member_detail'] = None
        
        return data
    
    def _is_admin(self, request):
        """관리자 여부 확인"""
        try:
            church_id = self.context.get('church_id')
            if church_id:
                church_user = request.user.church_users.get(church_id=church_id)
                return church_user.role in ['CHURCH_ADMIN', 'CHURCH_STAFF']
        except:
            pass
        return False


class OfferingCreateSerializer(serializers.ModelSerializer):
    """헌금 생성용 Serializer"""
    
    class Meta:
        model = Offering
        fields = ['member', 'amount', 'offering_type', 'date']
    
    def validate_amount(self, value):
        """헌금 금액 유효성 검사"""
        if value <= 0:
            raise serializers.ValidationError("헌금 금액은 0보다 커야 합니다.")
        if value > 10000000:  # 1천만원 제한
            raise serializers.ValidationError("헌금 금액이 너무 큽니다.")
        return value
    
    def validate_date(self, value):
        """헌금일 유효성 검사"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("헌금일은 오늘 이후일 수 없습니다.")
        return value
    
    def validate_member(self, value):
        """헌금자 유효성 검사"""
        if value:
            # 헌금자가 같은 교회 소속인지 확인
            church_id = self.context.get('church_id')
            if church_id and value.church_id != int(church_id):
                raise serializers.ValidationError("같은 교회 소속이 아닙니다.")
        return value
    
    def create(self, validated_data):
        """헌금 기록 생성"""
        user = self.context['request'].user
        church_id = self.context.get('church_id')
        
        validated_data['church_id'] = church_id
        validated_data['recorded_by'] = user
        
        return super().create(validated_data)


class OfferingUpdateSerializer(serializers.ModelSerializer):
    """헌금 수정용 Serializer"""
    
    class Meta:
        model = Offering
        fields = ['member', 'amount', 'offering_type', 'date']
    
    def validate_amount(self, value):
        """헌금 금액 유효성 검사"""
        if value <= 0:
            raise serializers.ValidationError("헌금 금액은 0보다 커야 합니다.")
        if value > 10000000:  # 1천만원 제한
            raise serializers.ValidationError("헌금 금액이 너무 큽니다.")
        return value
    
    def validate_date(self, value):
        """헌금일 유효성 검사"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("헌금일은 오늘 이후일 수 없습니다.")
        return value


class OfferingStatisticsSerializer(serializers.Serializer):
    """헌금 통계용 Serializer"""
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_count = serializers.IntegerField()
    average_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    offering_type_stats = serializers.ListField(child=serializers.DictField())
    monthly_stats = serializers.ListField(child=serializers.DictField())
    
    class Meta:
        fields = ['total_amount', 'total_count', 'average_amount', 'offering_type_stats', 'monthly_stats']
