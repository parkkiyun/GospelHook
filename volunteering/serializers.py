from rest_framework import serializers
from .models import VolunteerApplication, VolunteerRole, VolunteerAssignment, DEFAULT_VOLUNTEER_ROLES
from members.serializers import MemberSerializer
from users.models import DetailedPermission


class VolunteerApplicationListSerializer(serializers.ModelSerializer):
    """봉사 신청 목록용 Serializer"""
    applicant_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    is_application_open = serializers.SerializerMethodField()
    is_applied = serializers.SerializerMethodField()
    
    class Meta:
        model = VolunteerApplication
        fields = [
            'id', 'title', 'date', 'max_people', 'applicant_count',
            'is_full', 'is_application_open', 'is_applied', 'created_at'
        ]
    
    def get_applicant_count(self, obj):
        """신청자 수 반환"""
        return obj.applicants.count()
    
    def get_is_full(self, obj):
        """정원 초과 여부 반환"""
        if obj.max_people:
            return obj.applicants.count() >= obj.max_people
        return False
    
    def get_is_application_open(self, obj):
        """신청 가능 여부 반환"""
        from datetime import date
        return obj.date >= date.today()
    
    def get_is_applied(self, obj):
        """현재 사용자 신청 여부 반환"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                church_id = self.context.get('church_id')
                church_user = request.user.church_users.get(church_id=church_id)
                member = church_user.member
                return obj.applicants.filter(id=member.id).exists()
            except:
                pass
        return False


class VolunteerApplicationDetailSerializer(serializers.ModelSerializer):
    """봉사 신청 상세용 Serializer"""
    applicant_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    is_application_open = serializers.SerializerMethodField()
    is_applied = serializers.SerializerMethodField()
    applicants_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = VolunteerApplication
        fields = [
            'id', 'church', 'title', 'description', 'date', 'target_roles',
            'max_people', 'applicant_count', 'is_full', 'is_application_open',
            'is_applied', 'applicants_detail', 'created_at', 'updated_at'
        ]
        read_only_fields = ['church', 'created_at', 'updated_at']
    
    def get_applicant_count(self, obj):
        """신청자 수 반환"""
        return obj.applicants.count()
    
    def get_is_full(self, obj):
        """정원 초과 여부 반환"""
        if obj.max_people:
            return obj.applicants.count() >= obj.max_people
        return False
    
    def get_is_application_open(self, obj):
        """신청 가능 여부 반환"""
        from datetime import date
        return obj.date >= date.today()
    
    def get_is_applied(self, obj):
        """현재 사용자 신청 여부 반환"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                church_id = self.context.get('church_id')
                church_user = request.user.church_users.get(church_id=church_id)
                member = church_user.member
                return obj.applicants.filter(id=member.id).exists()
            except:
                pass
        return False
    
    def get_applicants_detail(self, obj):
        """신청자 목록 반환 (관리자용)"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # 관리자만 신청자 목록 볼 수 있음
            try:
                church_user = request.user.church_users.get(church_id=obj.church_id)
                if church_user.role in ['CHURCH_ADMIN', 'CHURCH_STAFF'] or request.user.is_superuser:
                    applicants = obj.applicants.all()
                    return [{
                        'id': applicant.id,
                        'name': applicant.name,
                        'phone': applicant.phone,
                        'email': applicant.email
                    } for applicant in applicants]
            except:
                pass
        return []


class VolunteerApplicationCreateSerializer(serializers.ModelSerializer):
    """봉사 신청 생성용 Serializer"""
    
    class Meta:
        model = VolunteerApplication
        fields = ['title', 'description', 'date', 'target_roles', 'max_people']
    
    def validate_title(self, value):
        """제목 유효성 검사"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("제목은 2자 이상이어야 합니다.")
        return value.strip()
    
    def validate_description(self, value):
        """설명 유효성 검사"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("설명은 5자 이상이어야 합니다.")
        return value.strip()
    
    def validate_date(self, value):
        """봉사일 유효성 검사"""
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("봉사일은 오늘 이후여야 합니다.")
        return value
    
    def validate_target_roles(self, value):
        """대상 직책 유효성 검사"""
        if value:
            valid_roles = ['CHURCH_ADMIN', 'CHURCH_STAFF', 'MEMBER', 'PASTOR', 'TEACHER']
            for role in value:
                if role not in valid_roles:
                    raise serializers.ValidationError(
                        f"유효하지 않은 직책입니다: {role}. "
                        f"유효한 직책: {', '.join(valid_roles)}"
                    )
        return value
    
    def validate_max_people(self, value):
        """최대 인원 유효성 검사"""
        if value is not None and value < 1:
            raise serializers.ValidationError("최대 인원은 1명 이상이어야 합니다.")
        return value


class VolunteerApplicationUpdateSerializer(serializers.ModelSerializer):
    """봉사 신청 수정용 Serializer"""
    
    class Meta:
        model = VolunteerApplication
        fields = ['title', 'description', 'date', 'target_roles', 'max_people']
    
    def validate_title(self, value):
        """제목 유효성 검사"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("제목은 2자 이상이어야 합니다.")
        return value.strip()
    
    def validate_description(self, value):
        """설명 유효성 검사"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("설명은 5자 이상이어야 합니다.")
        return value.strip()
    
    def validate_date(self, value):
        """봉사일 유효성 검사"""
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("봉사일은 오늘 이후여야 합니다.")
        return value
    
    def validate_target_roles(self, value):
        """대상 직책 유효성 검사"""
        if value:
            valid_roles = ['CHURCH_ADMIN', 'CHURCH_STAFF', 'MEMBER', 'PASTOR', 'TEACHER']
            for role in value:
                if role not in valid_roles:
                    raise serializers.ValidationError(
                        f"유효하지 않은 직책입니다: {role}. "
                        f"유효한 직책: {', '.join(valid_roles)}"
                    )
        return value
    
    def validate_max_people(self, value):
        """최대 인원 유효성 검사"""
        if value is not None and value < 1:
            raise serializers.ValidationError("최대 인원은 1명 이상이어야 합니다.")
        return value


class VolunteerRoleSerializer(serializers.ModelSerializer):
    """봉사 역할 시리얼라이저"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    required_level_display = serializers.CharField(source='get_required_level_display', read_only=True)
    current_assignees_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    target_group_names = serializers.SerializerMethodField()
    
    class Meta:
        model = VolunteerRole
        fields = [
            'id', 'church', 'name', 'code', 'description', 'category', 'category_display',
            'required_level', 'required_level_display', 'requires_training', 'training_requirements',
            'target_groups', 'target_group_names', 'default_permissions', 'is_active',
            'max_assignees', 'current_assignees_count', 'is_full', 'created_at', 'updated_at'
        ]
        read_only_fields = ['church', 'current_assignees_count', 'is_full', 'created_at', 'updated_at']
    
    def get_target_group_names(self, obj):
        """담당 그룹 이름 목록"""
        return [group.name for group in obj.target_groups.all()]
    
    def validate_code(self, value):
        """역할 코드 유효성 검사"""
        import re
        if not re.match(r'^[a-z0-9_]+$', value):
            raise serializers.ValidationError('역할 코드는 영문 소문자, 숫자, 언더스코어만 사용 가능합니다.')
        
        # 동일 교회 내 중복 검사
        church_id = self.context.get('church_id')
        if church_id:
            existing = VolunteerRole.objects.filter(
                church_id=church_id, 
                code=value
            ).exclude(pk=self.instance.pk if self.instance else None)
            if existing.exists():
                raise serializers.ValidationError('이미 존재하는 역할 코드입니다.')
        
        return value
    
    def validate_default_permissions(self, value):
        """기본 권한 유효성 검사"""
        if value:
            valid_permissions = set(DetailedPermission.objects.values_list('code', flat=True))
            invalid_permissions = [perm for perm in value if perm not in valid_permissions]
            if invalid_permissions:
                raise serializers.ValidationError(
                    f"유효하지 않은 권한 코드: {', '.join(invalid_permissions)}"
                )
        return value


class VolunteerRoleCreateSerializer(serializers.ModelSerializer):
    """봉사 역할 생성 시리얼라이저"""
    
    class Meta:
        model = VolunteerRole
        fields = [
            'name', 'code', 'description', 'category', 'required_level',
            'requires_training', 'training_requirements', 'target_groups',
            'default_permissions', 'max_assignees'
        ]
    
    def validate_code(self, value):
        """역할 코드 유효성 검사"""
        import re
        if not re.match(r'^[a-z0-9_]+$', value):
            raise serializers.ValidationError('역할 코드는 영문 소문자, 숫자, 언더스코어만 사용 가능합니다.')
        return value
    
    def create(self, validated_data):
        """봉사 역할 생성"""
        church_id = self.context.get('church_id')
        validated_data['church_id'] = church_id
        
        created_by = self.context['request'].user
        validated_data['created_by'] = created_by
        
        return super().create(validated_data)


class VolunteerAssignmentSerializer(serializers.ModelSerializer):
    """봉사 할당 시리얼라이저"""
    church_user_name = serializers.CharField(source='church_user.name', read_only=True)
    volunteer_role_name = serializers.CharField(source='volunteer_role.name', read_only=True)
    volunteer_role_category = serializers.CharField(source='volunteer_role.get_category_display', read_only=True)
    all_permissions = serializers.ListField(read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = VolunteerAssignment
        fields = [
            'id', 'church_user', 'church_user_name', 'volunteer_role', 'volunteer_role_name',
            'volunteer_role_category', 'assigned_date', 'start_date', 'end_date',
            'custom_permissions', 'all_permissions', 'is_active', 'notes',
            'approved_by', 'approved_by_name', 'approved_at'
        ]
        read_only_fields = ['assigned_date', 'approved_by', 'approved_at']
    
    def validate(self, attrs):
        """전체 유효성 검사"""
        church_user = attrs.get('church_user')
        volunteer_role = attrs.get('volunteer_role')
        
        if church_user and volunteer_role:
            # 동일 교회 확인
            if church_user.church != volunteer_role.church:
                raise serializers.ValidationError('사용자와 봉사 역할이 다른 교회에 속해 있습니다.')
            
            # 할당 가능 여부 확인
            can_assign, message = volunteer_role.can_assign_to(church_user)
            if not can_assign:
                raise serializers.ValidationError(message)
        
        return attrs
    
    def validate_custom_permissions(self, value):
        """개별 권한 유효성 검사"""
        if value:
            valid_permissions = set(DetailedPermission.objects.values_list('code', flat=True))
            invalid_permissions = [perm for perm in value if perm not in valid_permissions]
            if invalid_permissions:
                raise serializers.ValidationError(
                    f"유효하지 않은 권한 코드: {', '.join(invalid_permissions)}"
                )
        return value


class VolunteerAssignmentCreateSerializer(serializers.ModelSerializer):
    """봉사 할당 생성 시리얼라이저"""
    
    class Meta:
        model = VolunteerAssignment
        fields = ['church_user', 'volunteer_role', 'start_date', 'end_date', 'notes']
    
    def create(self, validated_data):
        """봉사 할당 생성"""
        from django.utils import timezone
        # 승인자 설정
        approved_by = self.context['request'].user
        validated_data['approved_by'] = approved_by
        validated_data['approved_at'] = timezone.now()
        
        return super().create(validated_data)


class VolunteerRoleTemplateSerializer(serializers.Serializer):
    """봉사 역할 템플릿 시리얼라이저"""
    name = serializers.CharField()
    code = serializers.CharField()
    category = serializers.CharField()
    description = serializers.CharField()
    required_level = serializers.CharField()
    requires_training = serializers.BooleanField()
    training_requirements = serializers.CharField(allow_blank=True)
    default_permissions = serializers.ListField(child=serializers.CharField())
    
    def create(self, validated_data):
        """템플릿으로부터 봉사 역할 생성"""
        church_id = self.context.get('church_id')
        validated_data['church_id'] = church_id
        validated_data['created_by'] = self.context['request'].user
        
        return VolunteerRole.objects.create(**validated_data)