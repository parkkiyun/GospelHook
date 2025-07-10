from rest_framework import serializers
from .models import Member, FamilyRelationship, FamilyTree
from groups.models import GroupMember


class MemberBasicSerializer(serializers.ModelSerializer):
    """기본 멤버 정보 시리얼라이저 (다른 앱에서 사용)"""
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Member
        fields = ['id', 'name', 'member_code', 'gender', 'age', 'phone', 'position']


class MemberSerializer(serializers.ModelSerializer):
    """교인 정보 시리얼라이저"""
    age = serializers.IntegerField(read_only=True)
    age_group = serializers.CharField(read_only=True)
    days_until_birthday = serializers.IntegerField(read_only=True)
    church_name = serializers.CharField(source='church.name', read_only=True)
    household_head_name = serializers.CharField(source='household.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Member
        fields = (
            'id', 'church', 'church_name', 'member_code', 'name', 'gender',
            'birth_date', 'lunar_birth', 'phone', 'email', 'address',
            'household', 'household_head_name', 'family_role', 'position',
            'baptism_date', 'confirmation_date', 'registration_date',
            'profile_image', 'status', 'is_active', 'auto_group_enabled',
            'notes', 'created_at', 'updated_at', 'created_by', 'created_by_name',
            'age', 'age_group', 'days_until_birthday'
        )
        read_only_fields = ('created_at', 'updated_at', 'age', 'age_group', 'days_until_birthday')
    
    def validate_member_code(self, value):
        """교인 번호 중복 검사"""
        church = self.context['request'].user.church_users.first().church
        if Member.objects.filter(church=church, member_code=value).exists():
            raise serializers.ValidationError("이미 사용 중인 교인 번호입니다.")
        return value


class MemberListSerializer(serializers.ModelSerializer):
    """교인 목록용 간단한 시리얼라이저"""
    age = serializers.IntegerField(read_only=True)
    age_group = serializers.CharField(read_only=True)
    
    class Meta:
        model = Member
        fields = (
            'id', 'member_code', 'name', 'gender', 'age', 'age_group',
            'phone', 'position', 'status', 'is_active', 'registration_date'
        )


class MemberCreateSerializer(serializers.ModelSerializer):
    """교인 생성용 시리얼라이저"""
    
    class Meta:
        model = Member
        fields = (
            'member_code', 'name', 'gender', 'birth_date', 'lunar_birth',
            'phone', 'email', 'address', 'household', 'family_role',
            'position', 'baptism_date', 'confirmation_date', 'registration_date',
            'profile_image', 'auto_group_enabled', 'notes'
        )
    
    def create(self, validated_data):
        """교인 생성 시 교회 정보 자동 설정"""
        request = self.context['request']
        church_user = request.user.church_users.first()
        
        if not church_user:
            raise serializers.ValidationError("교회에 속하지 않은 사용자입니다.")
        
        validated_data['church'] = church_user.church
        validated_data['created_by'] = request.user
        return super().create(validated_data)


class MemberDetailSerializer(serializers.ModelSerializer):
    """교인 상세 정보 시리얼라이저"""
    age = serializers.IntegerField(read_only=True)
    age_group = serializers.CharField(read_only=True)
    days_until_birthday = serializers.IntegerField(read_only=True)
    family_members = serializers.SerializerMethodField()
    group_memberships = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = (
            'id', 'church', 'member_code', 'name', 'gender', 'birth_date',
            'lunar_birth', 'phone', 'email', 'address', 'household',
            'family_role', 'position', 'baptism_date', 'confirmation_date',
            'registration_date', 'profile_image', 'status', 'is_active',
            'auto_group_enabled', 'notes', 'created_at', 'updated_at',
            'age', 'age_group', 'days_until_birthday', 'family_members',
            'group_memberships'
        )
        read_only_fields = ('created_at', 'updated_at')
    
    def get_family_members(self, obj):
        """가족 구성원 정보"""
        family_members = obj.get_family_members()
        return MemberListSerializer(family_members, many=True).data
    
    def get_group_memberships(self, obj):
        """소속 그룹 정보"""
        memberships = obj.group_memberships.filter(is_active=True).select_related('group')
        return [{
            'group_id': membership.group.id,
            'group_name': membership.group.name,
            'group_type': membership.group.get_group_type_display(),
            'role': membership.get_role_display(),
            'joined_date': membership.joined_date
        } for membership in memberships]


class MemberBirthdaySerializer(serializers.ModelSerializer):
    """생일자 목록용 시리얼라이저"""
    age = serializers.IntegerField(read_only=True)
    days_until_birthday = serializers.IntegerField(read_only=True)
    next_birthday = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = (
            'id', 'name', 'member_code', 'birth_date', 'phone',
            'age', 'days_until_birthday', 'next_birthday'
        )
    
    def get_next_birthday(self, obj):
        """다음 생일 날짜"""
        next_birthday = obj.get_next_birthday()
        return next_birthday.isoformat() if next_birthday else None


# 가족 관계 관련 시리얼라이저들

class FamilyRelationshipSerializer(serializers.ModelSerializer):
    """가족 관계 시리얼라이저"""
    from_member_detail = MemberBasicSerializer(source='from_member', read_only=True)
    to_member_detail = MemberBasicSerializer(source='to_member', read_only=True)
    relationship_display = serializers.CharField(source='get_relationship_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FamilyRelationship
        fields = [
            'id', 'from_member', 'from_member_detail', 'to_member', 'to_member_detail',
            'relationship', 'relationship_display', 'relationship_detail',
            'is_confirmed', 'notes', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'church', 'is_confirmed', 'created_at', 'updated_at']


class FamilyRelationshipCreateSerializer(serializers.ModelSerializer):
    """가족 관계 생성용 시리얼라이저"""
    from_member_id = serializers.IntegerField()
    to_member_id = serializers.IntegerField()
    
    class Meta:
        model = FamilyRelationship
        fields = [
            'from_member_id', 'to_member_id', 'relationship', 
            'relationship_detail', 'notes'
        ]
    
    def validate(self, attrs):
        """유효성 검사"""
        from_member_id = attrs.get('from_member_id')
        to_member_id = attrs.get('to_member_id')
        
        # 교인 존재 확인
        try:
            from_member = Member.objects.get(id=from_member_id)
            to_member = Member.objects.get(id=to_member_id)
            attrs['from_member'] = from_member
            attrs['to_member'] = to_member
        except Member.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 교인입니다.")
        
        # 자기 자신과의 관계 방지
        if from_member_id == to_member_id:
            raise serializers.ValidationError("자기 자신과는 가족 관계를 설정할 수 없습니다.")
        
        # 같은 교회 교인인지 확인
        if from_member.church != to_member.church:
            raise serializers.ValidationError("같은 교회 교인들간에만 가족 관계를 설정할 수 있습니다.")
        
        # 중복 관계 확인
        if FamilyRelationship.objects.filter(
            from_member=from_member,
            to_member=to_member,
            relationship=attrs.get('relationship')
        ).exists():
            raise serializers.ValidationError("이미 설정된 관계입니다.")
        
        return attrs


class FamilyRelationshipListSerializer(serializers.ModelSerializer):
    """가족 관계 목록용 시리얼라이저"""
    from_member_name = serializers.CharField(source='from_member.name', read_only=True)
    to_member_name = serializers.CharField(source='to_member.name', read_only=True)
    relationship_display = serializers.CharField(source='get_relationship_display', read_only=True)
    
    class Meta:
        model = FamilyRelationship
        fields = [
            'id', 'from_member_name', 'to_member_name', 'relationship',
            'relationship_display', 'relationship_detail', 'is_confirmed'
        ]


class FamilyTreeSerializer(serializers.ModelSerializer):
    """가족 계보 시리얼라이저"""
    root_member_detail = MemberBasicSerializer(source='root_member', read_only=True)
    family_members_detail = MemberBasicSerializer(source='family_members', many=True, read_only=True)
    family_statistics = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FamilyTree
        fields = [
            'id', 'family_name', 'root_member', 'root_member_detail',
            'family_members', 'family_members_detail', 'description',
            'is_active', 'family_statistics', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_family_statistics(self, obj):
        """가족 통계 정보"""
        return obj.get_family_statistics()


class FamilyTreeCreateSerializer(serializers.ModelSerializer):
    """가족 계보 생성용 시리얼라이저"""
    root_member_id = serializers.IntegerField()
    family_member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = FamilyTree
        fields = [
            'family_name', 'root_member_id', 'family_member_ids', 
            'description', 'is_active'
        ]
    
    def validate(self, attrs):
        """유효성 검사"""
        root_member_id = attrs.get('root_member_id')
        
        try:
            root_member = Member.objects.get(id=root_member_id)
            attrs['root_member'] = root_member
        except Member.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 대표 교인입니다.")
        
        # 가족 구성원 유효성 검사
        family_member_ids = attrs.get('family_member_ids', [])
        if family_member_ids:
            family_members = Member.objects.filter(
                id__in=family_member_ids,
                church=root_member.church
            )
            if family_members.count() != len(family_member_ids):
                raise serializers.ValidationError("유효하지 않은 가족 구성원이 포함되어 있습니다.")
            attrs['family_members'] = family_members
        
        return attrs
    
    def create(self, validated_data):
        """가족 계보 생성"""
        family_members = validated_data.pop('family_members', [])
        family_tree = super().create(validated_data)
        
        # 가족 구성원 추가 (대표 교인 포함)
        family_tree.family_members.add(family_tree.root_member)
        if family_members:
            family_tree.family_members.add(*family_members)
        
        return family_tree


class MemberFamilyTreeSerializer(serializers.ModelSerializer):
    """교인의 가족 관계도 데이터 시리얼라이저"""
    family_tree_data = serializers.SerializerMethodField()
    family_relationships = serializers.SerializerMethodField()
    family_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'name', 'member_code', 'gender', 'age',
            'family_tree_data', 'family_relationships', 'family_summary'
        ]
    
    def get_family_tree_data(self, obj):
        """가족 관계도 그래프 데이터"""
        return obj.get_family_tree_data()
    
    def get_family_relationships(self, obj):
        """상세 가족 관계 목록"""
        relationships = obj.get_family_relationships()
        return FamilyRelationshipListSerializer(relationships, many=True).data
    
    def get_family_summary(self, obj):
        """가족 관계 요약"""
        return {
            'spouse': obj.get_spouse().name if obj.get_spouse() else None,
            'children_count': len(obj.get_children()),
            'parents_count': len(obj.get_parents()),
            'siblings_count': len(obj.get_siblings()),
            'total_relationships': obj.get_family_relationships().count()
        }
