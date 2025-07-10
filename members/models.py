from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta


class Member(models.Model):
    """교인 정보 모델"""
    
    class Gender(models.TextChoices):
        MALE = 'M', '남성'
        FEMALE = 'F', '여성'
    
    class MemberStatus(models.TextChoices):
        ACTIVE = 'active', '활동 교인'
        INACTIVE = 'inactive', '비활동 교인'
        MOVED = 'moved', '이전'
        DECEASED = 'deceased', '소천'
    
    # 기본 정보
    church = models.ForeignKey(
        'church.Church', 
        on_delete=models.CASCADE, 
        related_name='members',
        verbose_name='소속 교회'
    )
    member_code = models.CharField(
        max_length=20,
        verbose_name='교인 번호',
        help_text='교회별 고유 교인 번호'
    )
    name = models.CharField(max_length=50, verbose_name='이름')
    gender = models.CharField(
        max_length=1, 
        choices=Gender.choices, 
        null=True, 
        blank=True, 
        verbose_name='성별'
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name='생년월일')
    lunar_birth = models.BooleanField(default=False, verbose_name='음력 생일')
    
    # 연락처 정보
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name='휴대폰',
        validators=[RegexValidator(regex=r'^\d{3}-\d{3,4}-\d{4}$', message='올바른 전화번호 형식이 아닙니다.')]
    )
    email = models.EmailField(blank=True, verbose_name='이메일')
    address = models.TextField(blank=True, verbose_name='주소')
    
    # 가족 관계
    household = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='family_members',
        verbose_name='세대주'
    )
    family_role = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='가족 내 역할',
        help_text='세대주, 배우자, 자녀 등'
    )
    
    # 교회 내 정보
    position = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='직분',
        help_text='목사, 전도사, 장로, 권사, 집사 등'
    )
    baptism_date = models.DateField(null=True, blank=True, verbose_name='세례일')
    confirmation_date = models.DateField(null=True, blank=True, verbose_name='입교일')
    registration_date = models.DateField(default=date.today, verbose_name='등록일')
    
    # 소속 정보
    groups = models.ManyToManyField(
        'groups.Group',
        through='groups.GroupMember',
        related_name='members',
        verbose_name='소속 그룹'
    )
    
    # 사진
    profile_image = models.ImageField(
        upload_to='members/profiles/', 
        null=True, 
        blank=True, 
        verbose_name='프로필 사진'
    )
    
    # 상태 정보
    status = models.CharField(
        max_length=20,
        choices=MemberStatus.choices,
        default=MemberStatus.ACTIVE,
        verbose_name='상태'
    )
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    auto_group_enabled = models.BooleanField(default=True, verbose_name='자동 진급 대상')
    
    # 메모
    notes = models.TextField(blank=True, verbose_name='메모')
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_members',
        verbose_name='생성자'
    )
    
    class Meta:
        db_table = 'members'
        verbose_name = '교인'
        verbose_name_plural = '교인들'
        unique_together = [['church', 'member_code']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['church', 'status']),
            models.Index(fields=['church', 'birth_date']),
            models.Index(fields=['church', 'household']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.member_code})"
    
    @property
    def age(self):
        """현재 나이 계산"""
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None
    
    @property
    def age_group(self):
        """연령대 반환"""
        age = self.age
        if age is None:
            return None
        elif age < 8:
            return '영유아부'
        elif age < 14:
            return '유년부'
        elif age < 17:
            return '중등부'
        elif age < 20:
            return '고등부'
        elif age < 30:
            return '청년부'
        elif age < 65:
            return '장년부'
        else:
            return '노년부'
    
    def get_next_birthday(self):
        """다음 생일 날짜 계산"""
        if not self.birth_date:
            return None
            
        today = date.today()
        this_year_birthday = self.birth_date.replace(year=today.year)
        
        if this_year_birthday < today:
            return self.birth_date.replace(year=today.year + 1)
        return this_year_birthday
    
    def days_until_birthday(self):
        """생일까지 남은 일수"""
        next_birthday = self.get_next_birthday()
        if next_birthday:
            return (next_birthday - date.today()).days
        return None
    
    def get_family_members(self):
        """가족 구성원 목록 (기존 household 기반)"""
        if self.household:
            # 자신이 세대주인 경우
            if self.household == self:
                return Member.objects.filter(household=self).exclude(id=self.id)
            # 세대원인 경우 전체 가족 반환
            else:
                return Member.objects.filter(
                    models.Q(household=self.household) | models.Q(id=self.household.id)
                ).exclude(id=self.id)
        return Member.objects.none()
    
    def get_family_relationships(self):
        """이 교인의 모든 가족 관계 조회"""
        return FamilyRelationship.objects.filter(
            from_member=self
        ).select_related('to_member')
    
    def get_relatives_by_type(self, relationship_type):
        """특정 관계의 가족 구성원 조회"""
        return FamilyRelationship.objects.filter(
            from_member=self,
            relationship=relationship_type
        ).select_related('to_member')
    
    def get_spouse(self):
        """배우자 조회"""
        spouse_rel = self.get_relatives_by_type(FamilyRelationship.RelationshipType.SPOUSE).first()
        return spouse_rel.to_member if spouse_rel else None
    
    def get_children(self):
        """자녀 목록"""
        return [rel.to_member for rel in self.get_relatives_by_type(FamilyRelationship.RelationshipType.CHILD)]
    
    def get_parents(self):
        """부모 목록"""
        return [rel.to_member for rel in self.get_relatives_by_type(FamilyRelationship.RelationshipType.PARENT)]
    
    def get_siblings(self):
        """형제자매 목록"""
        return [rel.to_member for rel in self.get_relatives_by_type(FamilyRelationship.RelationshipType.SIBLING)]
    
    def add_family_relationship(self, to_member, relationship, relationship_detail='', created_by=None):
        """가족 관계 추가"""
        return FamilyRelationship.objects.create(
            church=self.church,
            from_member=self,
            to_member=to_member,
            relationship=relationship,
            relationship_detail=relationship_detail,
            created_by=created_by
        )
    
    def get_family_tree_data(self):
        """가족 관계도 데이터 생성 (그래프 형태)"""
        relationships = self.get_family_relationships()
        
        nodes = [{'id': self.id, 'name': self.name, 'gender': self.gender, 'is_self': True}]
        edges = []
        
        for rel in relationships:
            # 관계된 교인 노드 추가
            if not any(node['id'] == rel.to_member.id for node in nodes):
                nodes.append({
                    'id': rel.to_member.id,
                    'name': rel.to_member.name,
                    'gender': rel.to_member.gender,
                    'is_self': False
                })
            
            # 관계 엣지 추가
            edges.append({
                'from': self.id,
                'to': rel.to_member.id,
                'relationship': rel.relationship,
                'relationship_display': rel.get_relationship_display(),
                'relationship_detail': rel.relationship_detail
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'center_member': {
                'id': self.id,
                'name': self.name,
                'gender': self.gender
            }
        }


class FamilyRelationship(models.Model):
    """가족 관계 모델"""
    
    class RelationshipType(models.TextChoices):
        SPOUSE = 'spouse', '배우자'
        PARENT = 'parent', '부모'
        CHILD = 'child', '자녀'
        SIBLING = 'sibling', '형제자매'
        GRANDPARENT = 'grandparent', '조부모'
        GRANDCHILD = 'grandchild', '손자녀'
        UNCLE_AUNT = 'uncle_aunt', '삼촌/이모/고모/외삼촌'
        NEPHEW_NIECE = 'nephew_niece', '조카'
        COUSIN = 'cousin', '사촌'
        INLAW = 'inlaw', '인척'
        OTHER = 'other', '기타'
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='family_relationships',
        verbose_name='교회'
    )
    from_member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='family_relations_from',
        verbose_name='기준 교인'
    )
    to_member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='family_relations_to',
        verbose_name='관계 교인'
    )
    relationship = models.CharField(
        max_length=20,
        choices=RelationshipType.choices,
        verbose_name='관계'
    )
    relationship_detail = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='관계 상세',
        help_text='예: 큰아들, 둘째딸, 시어머니 등'
    )
    is_confirmed = models.BooleanField(
        default=False,
        verbose_name='확인됨',
        help_text='양방향 관계가 모두 설정되었는지 여부'
    )
    notes = models.TextField(blank=True, verbose_name='메모')
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_family_relationships',
        verbose_name='생성자'
    )
    
    class Meta:
        db_table = 'family_relationships'
        verbose_name = '가족 관계'
        verbose_name_plural = '가족 관계들'
        unique_together = [['from_member', 'to_member', 'relationship']]
        ordering = ['from_member__name', 'relationship']
        indexes = [
            models.Index(fields=['church', 'from_member']),
            models.Index(fields=['church', 'to_member']),
            models.Index(fields=['relationship']),
        ]
    
    def __str__(self):
        return f"{self.from_member.name} - {self.get_relationship_display()} - {self.to_member.name}"
    
    def clean(self):
        """유효성 검사"""
        from django.core.exceptions import ValidationError
        
        # 자기 자신과의 관계 방지
        if self.from_member == self.to_member:
            raise ValidationError("자기 자신과는 가족 관계를 설정할 수 없습니다.")
        
        # 같은 교회 내 교인들만 관계 설정 가능
        if self.from_member.church != self.to_member.church:
            raise ValidationError("같은 교회 교인들간에만 가족 관계를 설정할 수 있습니다.")
    
    def save(self, *args, **kwargs):
        self.church = self.from_member.church
        self.clean()
        super().save(*args, **kwargs)
        
        # 역방향 관계 자동 생성
        self.create_reverse_relationship()
    
    def create_reverse_relationship(self):
        """역방향 관계 자동 생성"""
        reverse_map = {
            self.RelationshipType.SPOUSE: self.RelationshipType.SPOUSE,
            self.RelationshipType.PARENT: self.RelationshipType.CHILD,
            self.RelationshipType.CHILD: self.RelationshipType.PARENT,
            self.RelationshipType.SIBLING: self.RelationshipType.SIBLING,
            self.RelationshipType.GRANDPARENT: self.RelationshipType.GRANDCHILD,
            self.RelationshipType.GRANDCHILD: self.RelationshipType.GRANDPARENT,
            self.RelationshipType.UNCLE_AUNT: self.RelationshipType.NEPHEW_NIECE,
            self.RelationshipType.NEPHEW_NIECE: self.RelationshipType.UNCLE_AUNT,
            self.RelationshipType.COUSIN: self.RelationshipType.COUSIN,
            self.RelationshipType.INLAW: self.RelationshipType.INLAW,
            self.RelationshipType.OTHER: self.RelationshipType.OTHER,
        }
        
        reverse_relationship = reverse_map.get(self.relationship)
        if reverse_relationship:
            # 이미 역방향 관계가 존재하는지 확인
            existing = FamilyRelationship.objects.filter(
                from_member=self.to_member,
                to_member=self.from_member,
                relationship=reverse_relationship
            ).first()
            
            if not existing:
                FamilyRelationship.objects.create(
                    church=self.church,
                    from_member=self.to_member,
                    to_member=self.from_member,
                    relationship=reverse_relationship,
                    is_confirmed=True,
                    created_by=self.created_by
                )
            
            # 양방향 관계 확인 상태 업데이트
            self.is_confirmed = True
            FamilyRelationship.objects.filter(id=self.id).update(is_confirmed=True)
            if existing:
                existing.is_confirmed = True
                existing.save()


class FamilyTree(models.Model):
    """가족 계보 모델 (가족 단위 관리)"""
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='family_trees',
        verbose_name='교회'
    )
    family_name = models.CharField(
        max_length=50,
        verbose_name='가족명',
        help_text='예: 김씨 가족, 이철수 가족'
    )
    root_member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='rooted_family_trees',
        verbose_name='가족 대표',
        help_text='가족의 대표가 되는 교인 (보통 세대주)'
    )
    family_members = models.ManyToManyField(
        Member,
        related_name='family_trees',
        verbose_name='가족 구성원'
    )
    description = models.TextField(
        blank=True,
        verbose_name='설명'
    )
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_family_trees',
        verbose_name='생성자'
    )
    
    class Meta:
        db_table = 'family_trees'
        verbose_name = '가족 계보'
        verbose_name_plural = '가족 계보들'
        unique_together = [['church', 'family_name']]
        ordering = ['family_name']
        indexes = [
            models.Index(fields=['church', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.family_name}"
    
    def get_family_relationships(self):
        """이 가족 내 모든 관계 조회"""
        member_ids = self.family_members.values_list('id', flat=True)
        return FamilyRelationship.objects.filter(
            from_member__id__in=member_ids,
            to_member__id__in=member_ids
        )
    
    def get_family_statistics(self):
        """가족 통계 정보"""
        members = self.family_members.all()
        return {
            'total_members': members.count(),
            'male_count': members.filter(gender=Member.Gender.MALE).count(),
            'female_count': members.filter(gender=Member.Gender.FEMALE).count(),
            'age_groups': {},  # TODO: 연령대별 통계
            'active_members': members.filter(status=Member.MemberStatus.ACTIVE).count(),
        }