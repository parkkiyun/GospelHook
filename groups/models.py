from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Group(models.Model):
    """교회 내 그룹/부서 모델"""
    
    class GroupType(models.TextChoices):
        DEPARTMENT = 'department', '부서'
        DISTRICT = 'district', '구역'
        CELL = 'cell', '셀/소그룹'
        CHOIR = 'choir', '찬양대'
        COMMITTEE = 'committee', '위원회'
        MINISTRY = 'ministry', '사역팀'
        OTHER = 'other', '기타'
    
    class ManagementType(models.TextChoices):
        AUTO = 'auto', '자동 (나이 기준)'
        MANUAL = 'manual', '수동'
        HYBRID = 'hybrid', '혼합 (자동+수동)'
    
    # 기본 정보
    church = models.ForeignKey(
        'church.Church', 
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='소속 교회'
    )
    name = models.CharField(max_length=100, verbose_name='그룹명')
    code = models.CharField(max_length=20, blank=True, verbose_name='그룹 코드')
    description = models.TextField(blank=True, verbose_name='설명')
    
    # 그룹 유형
    group_type = models.CharField(
        max_length=20, 
        choices=GroupType.choices,
        default=GroupType.DEPARTMENT,
        verbose_name='그룹 종류'
    )
    
    # 계층 구조
    parent_group = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_groups',
        verbose_name='상위 그룹'
    )
    order = models.IntegerField(default=0, verbose_name='정렬 순서')
    
    # 관리 방식
    management_type = models.CharField(
        max_length=10, 
        choices=ManagementType.choices, 
        default=ManagementType.MANUAL, 
        verbose_name='관리 유형'
    )
    
    # 자동 관리 기준 (나이)
    age_min = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name='최소 연령',
        help_text='자동 관리 시 최소 나이'
    )
    age_max = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name='최대 연령',
        help_text='자동 관리 시 최대 나이'
    )
    
    # 담당자
    leader = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leading_groups',
        verbose_name='그룹장'
    )
    
    # 모임 정보
    meeting_day = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='정기 모임 요일',
        help_text='예: 주일, 수요일, 매주 금요일'
    )
    meeting_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='모임 시간'
    )
    meeting_place = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='모임 장소'
    )
    
    # 상태
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    max_members = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='최대 인원',
        help_text='그룹 최대 인원 제한'
    )
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups',
        verbose_name='생성자'
    )
    
    class Meta:
        db_table = 'groups'
        verbose_name = '그룹'
        verbose_name_plural = '그룹들'
        unique_together = [['church', 'code']]
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['church', 'group_type']),
            models.Index(fields=['church', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_group_type_display()})"
    
    def clean(self):
        """유효성 검사"""
        if self.management_type in ['auto', 'hybrid']:
            if self.age_min is None or self.age_max is None:
                raise ValidationError('자동 관리 그룹은 나이 범위를 설정해야 합니다.')
            if self.age_min > self.age_max:
                raise ValidationError('최소 나이는 최대 나이보다 작아야 합니다.')
    
    @property
    def member_count(self):
        """현재 그룹 인원 수"""
        return self.group_members.filter(is_active=True).count()
    
    @property
    def is_full(self):
        """정원 초과 여부"""
        if self.max_members:
            return self.member_count >= self.max_members
        return False
    
    def get_hierarchy_name(self):
        """계층 구조를 포함한 전체 이름"""
        if self.parent_group:
            return f"{self.parent_group.get_hierarchy_name()} > {self.name}"
        return self.name
    
    def get_all_sub_groups(self):
        """모든 하위 그룹 조회 (재귀)"""
        sub_groups = list(self.sub_groups.all())
        for sub_group in self.sub_groups.all():
            sub_groups.extend(sub_group.get_all_sub_groups())
        return sub_groups
    
    def can_add_member(self, member):
        """멤버 추가 가능 여부 확인"""
        if self.is_full:
            return False, "그룹 정원이 초과되었습니다."
            
        if self.management_type in ['auto', 'hybrid'] and member.age:
            if member.age < self.age_min or member.age > self.age_max:
                return False, f"나이 제한 ({self.age_min}-{self.age_max}세)에 맞지 않습니다."
        
        return True, None


class GroupMember(models.Model):
    """그룹-멤버 연결 모델"""
    
    class MemberRole(models.TextChoices):
        LEADER = 'leader', '그룹장'
        SUB_LEADER = 'sub_leader', '부그룹장'
        MEMBER = 'member', '그룹원'
        SECRETARY = 'secretary', '총무'
    
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='group_members',
        verbose_name='그룹'
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='group_memberships',
        verbose_name='멤버'
    )
    role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
        default=MemberRole.MEMBER,
        verbose_name='역할'
    )
    joined_date = models.DateField(
        default=timezone.now,
        verbose_name='가입일'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성 상태'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='메모'
    )
    
    class Meta:
        db_table = 'group_members'
        verbose_name = '그룹 멤버'
        verbose_name_plural = '그룹 멤버들'
        unique_together = [['group', 'member']]
        ordering = ['-role', 'member__name']
    
    def __str__(self):
        return f"{self.member.name} - {self.group.name} ({self.get_role_display()})"