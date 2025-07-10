from rest_framework import serializers
from .models import EducationProgram, EducationRegistration
from members.serializers import MemberSerializer


class EducationProgramListSerializer(serializers.ModelSerializer):
    """교육 프로그램 목록용 Serializer"""
    registration_count = serializers.SerializerMethodField()
    is_registration_open = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    
    class Meta:
        model = EducationProgram
        fields = [
            'id', 'title', 'date', 'registration_deadline', 'max_people',
            'registration_count', 'is_registration_open', 'is_full', 'created_at'
        ]
    
    def get_registration_count(self, obj):
        """등록 인원 수 반환"""
        return obj.educationregistration_set.exclude(status='CANCELED').count()
    
    def get_is_registration_open(self, obj):
        """등록 가능 여부 반환"""
        from datetime import date
        return obj.registration_deadline >= date.today()
    
    def get_is_full(self, obj):
        """정원 초과 여부 반환"""
        if obj.max_people:
            registration_count = obj.educationregistration_set.exclude(status='CANCELED').count()
            return registration_count >= obj.max_people
        return False


class EducationProgramDetailSerializer(serializers.ModelSerializer):
    """교육 프로그램 상세용 Serializer"""
    registration_count = serializers.SerializerMethodField()
    is_registration_open = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    registrations = serializers.SerializerMethodField()
    
    class Meta:
        model = EducationProgram
        fields = [
            'id', 'church', 'title', 'description', 'date', 'registration_deadline',
            'target_roles', 'max_people', 'registration_count', 'is_registration_open',
            'is_full', 'registrations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['church', 'created_at', 'updated_at']
    
    def get_registration_count(self, obj):
        """등록 인원 수 반환"""
        return obj.educationregistration_set.exclude(status='CANCELED').count()
    
    def get_is_registration_open(self, obj):
        """등록 가능 여부 반환"""
        from datetime import date
        return obj.registration_deadline >= date.today()
    
    def get_is_full(self, obj):
        """정원 초과 여부 반환"""
        if obj.max_people:
            registration_count = obj.educationregistration_set.exclude(status='CANCELED').count()
            return registration_count >= obj.max_people
        return False
    
    def get_registrations(self, obj):
        """등록 목록 반환 (관리자용)"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # 관리자만 등록 목록 볼 수 있음
            try:
                church_user = request.user.church_users.get(church_id=obj.church_id)
                if church_user.role in ['CHURCH_ADMIN', 'CHURCH_STAFF'] or request.user.is_superuser:
                    registrations = obj.educationregistration_set.select_related('member').all()
                    return [{
                        'id': reg.id,
                        'member_name': reg.member.name,
                        'member_phone': reg.member.phone,
                        'status': reg.status,
                        'registered_at': reg.registered_at
                    } for reg in registrations]
            except:
                pass
        return []


class EducationProgramCreateSerializer(serializers.ModelSerializer):
    """교육 프로그램 생성용 Serializer"""
    
    class Meta:
        model = EducationProgram
        fields = [
            'title', 'description', 'date', 'registration_deadline',
            'target_roles', 'max_people'
        ]
    
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
    
    def validate(self, data):
        """교차 유효성 검사"""
        if data['date'] <= data['registration_deadline']:
            raise serializers.ValidationError("교육일은 등록 마감일보다 이후여야 합니다.")
        return data
    
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


class EducationRegistrationSerializer(serializers.ModelSerializer):
    """교육 등록 Serializer"""
    member_detail = MemberSerializer(source='member', read_only=True)
    program_title = serializers.CharField(source='program.title', read_only=True)
    program_date = serializers.DateField(source='program.date', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EducationRegistration
        fields = [
            'id', 'program', 'program_title', 'program_date', 'member',
            'member_detail', 'status', 'status_display', 'registered_at'
        ]
        read_only_fields = ['member', 'registered_at']
    
    def validate_program(self, value):
        """프로그램 유효성 검사"""
        from datetime import date
        
        # 등록 마감일 확인
        if value.registration_deadline < date.today():
            raise serializers.ValidationError("등록 마감일이 지났습니다.")
        
        # 정원 확인
        if value.max_people:
            current_count = value.educationregistration_set.exclude(status='CANCELED').count()
            if current_count >= value.max_people:
                raise serializers.ValidationError("정원이 초과되었습니다.")
        
        return value


class EducationRegistrationCreateSerializer(serializers.ModelSerializer):
    """교육 등록 생성용 Serializer"""
    
    class Meta:
        model = EducationRegistration
        fields = ['program']
    
    def validate_program(self, value):
        """프로그램 유효성 검사"""
        from datetime import date
        
        # 등록 마감일 확인
        if value.registration_deadline < date.today():
            raise serializers.ValidationError("등록 마감일이 지났습니다.")
        
        # 정원 확인
        if value.max_people:
            current_count = value.educationregistration_set.exclude(status='CANCELED').count()
            if current_count >= value.max_people:
                raise serializers.ValidationError("정원이 초과되었습니다.")
        
        return value
    
    def create(self, validated_data):
        """교육 등록 생성"""
        user = self.context['request'].user
        
        # 사용자의 교회 멤버 정보 가져오기
        try:
            church_user = user.church_users.get(church_id=validated_data['program'].church_id)
            member = church_user.member
        except:
            raise serializers.ValidationError("교회 멤버 정보를 찾을 수 없습니다.")
        
        # 중복 등록 확인
        if EducationRegistration.objects.filter(
            program=validated_data['program'],
            member=member
        ).exists():
            raise serializers.ValidationError("이미 등록된 프로그램입니다.")
        
        validated_data['member'] = member
        return super().create(validated_data)