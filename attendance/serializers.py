from rest_framework import serializers
from .models import Attendance, AttendanceTemplate
from members.serializers import MemberBasicSerializer
from groups.serializers import GroupListSerializer


class AttendanceSerializer(serializers.ModelSerializer):
    """출석 기록 시리얼라이저"""
    member = MemberBasicSerializer(read_only=True)
    member_id = serializers.IntegerField(write_only=True)
    group = GroupListSerializer(read_only=True)
    group_id = serializers.IntegerField(write_only=True, required=False)
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'member', 'member_id', 'group', 'group_id', 'date', 'status',
            'worship_type', 'arrival_time', 'departure_time', 'duration',
            'notes', 'recorded_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_duration(self, obj):
        """예배 참석 시간 계산"""
        duration = obj.get_duration()
        if duration:
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}시간 {minutes}분"
        return None


class AttendanceListSerializer(serializers.ModelSerializer):
    """출석 목록용 시리얼라이저"""
    member_name = serializers.CharField(source='member.name', read_only=True)
    member_code = serializers.CharField(source='member.member_code', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'member_name', 'member_code', 'date', 'status',
            'worship_type', 'arrival_time', 'departure_time', 'notes'
        ]


class AttendanceCreateSerializer(serializers.ModelSerializer):
    """출석 생성용 시리얼라이저"""
    member_id = serializers.IntegerField()
    group_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = Attendance
        fields = [
            'member_id', 'group_id', 'date', 'status', 'worship_type',
            'arrival_time', 'departure_time', 'notes'
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


class AttendanceBulkCreateSerializer(serializers.Serializer):
    """대량 출석 생성용 시리얼라이저"""
    date = serializers.DateField()
    worship_type = serializers.ChoiceField(choices=Attendance.WorshipType.choices)
    group_id = serializers.IntegerField(required=False)
    attendances = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    def validate_attendances(self, value):
        """출석 데이터 유효성 검사"""
        if not value:
            raise serializers.ValidationError("출석 데이터가 비어있습니다.")
        
        for attendance in value:
            if 'member_id' not in attendance:
                raise serializers.ValidationError("member_id는 필수입니다.")
            if 'status' not in attendance:
                raise serializers.ValidationError("status는 필수입니다.")
            if attendance['status'] not in [choice[0] for choice in Attendance.AttendanceStatus.choices]:
                raise serializers.ValidationError(f"유효하지 않은 출석 상태입니다: {attendance['status']}")
        
        return value


class AttendanceStatsSerializer(serializers.Serializer):
    """출석 통계용 시리얼라이저"""
    total_records = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
    worship_type_stats = serializers.DictField()
    weekly_stats = serializers.ListField()


class AttendanceTemplateSerializer(serializers.ModelSerializer):
    """출석 템플릿 시리얼라이저"""
    target_groups = GroupListSerializer(many=True, read_only=True)
    target_group_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    next_occurrence = serializers.DateField(source='get_next_occurrence', read_only=True)
    
    class Meta:
        model = AttendanceTemplate
        fields = [
            'id', 'name', 'worship_type', 'day_of_week', 'start_time', 'end_time',
            'target_groups', 'target_group_ids', 'is_active', 'auto_check_enabled',
            'auto_check_time', 'next_occurrence', 'created_by_name', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """템플릿 생성"""
        target_group_ids = validated_data.pop('target_group_ids', [])
        template = AttendanceTemplate.objects.create(**validated_data)
        
        if target_group_ids:
            from groups.models import Group
            groups = Group.objects.filter(id__in=target_group_ids)
            template.target_groups.set(groups)
        
        return template
    
    def update(self, instance, validated_data):
        """템플릿 수정"""
        target_group_ids = validated_data.pop('target_group_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if target_group_ids is not None:
            from groups.models import Group
            groups = Group.objects.filter(id__in=target_group_ids)
            instance.target_groups.set(groups)
        
        return instance


class AttendanceTemplateListSerializer(serializers.ModelSerializer):
    """출석 템플릿 목록용 시리얼라이저"""
    target_group_count = serializers.IntegerField(source='target_groups.count', read_only=True)
    next_occurrence = serializers.DateField(source='get_next_occurrence', read_only=True)
    
    class Meta:
        model = AttendanceTemplate
        fields = [
            'id', 'name', 'worship_type', 'day_of_week', 'start_time',
            'end_time', 'target_group_count', 'is_active', 'next_occurrence'
        ]