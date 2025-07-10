from django.db import models
from django.core.exceptions import ValidationError


class VolunteerRole(models.Model):
    """
    교회별 봉사/사역 역할 정의 모델
    각 교회마다 고유한 봉사 역할을 정의할 수 있음
    """
    class RoleCategory(models.TextChoices):
        DEPARTMENT = 'department', '부서 사역'
        WORSHIP = 'worship', '예배 사역'
        EDUCATION = 'education', '교육 사역'
        CARE = 'care', '돌봄 사역'
        OUTREACH = 'outreach', '전도/선교 사역'
        FACILITY = 'facility', '시설 관리'
        MEDIA = 'media', '미디어/기술'
        ADMINISTRATION = 'administration', '행정 업무'
        SPECIAL = 'special', '특별 사역'
        OTHER = 'other', '기타'
    
    class RequiredLevel(models.TextChoices):
        ANYONE = 'anyone', '누구나'
        MEMBER = 'member', '교인만'
        EXPERIENCED = 'experienced', '경험자'
        TRAINED = 'trained', '훈련 이수자'
        APPOINTED = 'appointed', '임명된 자'
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='volunteer_roles',
        verbose_name='소속 교회'
    )
    name = models.CharField(max_length=100, verbose_name='역할명')
    code = models.CharField(
        max_length=50,
        verbose_name='역할 코드',
        help_text='영문/숫자로 구성된 고유 코드 (예: children_teacher)'
    )
    description = models.TextField(blank=True, verbose_name='역할 설명')
    category = models.CharField(
        max_length=20,
        choices=RoleCategory.choices,
        default=RoleCategory.OTHER,
        verbose_name='카테고리'
    )
    
    # 요구사항
    required_level = models.CharField(
        max_length=20,
        choices=RequiredLevel.choices,
        default=RequiredLevel.MEMBER,
        verbose_name='필요 자격'
    )
    requires_training = models.BooleanField(
        default=False,
        verbose_name='교육 필수'
    )
    training_requirements = models.TextField(
        blank=True,
        verbose_name='교육 요구사항'
    )
    
    # 담당 범위
    target_groups = models.ManyToManyField(
        'groups.Group',
        blank=True,
        verbose_name='담당 그룹',
        help_text='이 역할이 관리하는 그룹들'
    )
    
    # 기본 권한 설정
    default_permissions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='기본 권한',
        help_text='이 역할에 자동으로 부여되는 권한 목록'
    )
    
    # 상태
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    max_assignees = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='최대 임명 인원'
    )
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_volunteer_roles',
        verbose_name='생성자'
    )
    
    class Meta:
        db_table = 'volunteer_roles'
        verbose_name = '봉사 역할'
        verbose_name_plural = '봉사 역할들'
        unique_together = [['church', 'code']]
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['church', 'category']),
            models.Index(fields=['church', 'is_active']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.church.name})"
    
    def clean(self):
        """유효성 검사"""
        if self.requires_training and not self.training_requirements:
            raise ValidationError('교육이 필수인 경우 교육 요구사항을 입력해야 합니다.')
    
    @property 
    def current_assignees_count(self):
        """현재 임명된 인원 수"""
        return self.volunteer_assignments.filter(is_active=True).count()
    
    @property
    def is_full(self):
        """정원 초과 여부"""
        if self.max_assignees:
            return self.current_assignees_count >= self.max_assignees
        return False
    
    def can_assign_to(self, church_user):
        """특정 사용자에게 이 역할을 할당할 수 있는지 확인"""
        if not self.is_active:
            return False, "비활성화된 역할입니다."
        
        if self.is_full:
            return False, "정원이 초과되었습니다."
        
        # 자격 요구사항 확인
        if self.required_level == 'member' and church_user.role == 'member':
            pass  # OK
        elif self.required_level == 'experienced':
            # 추가 로직 필요
            pass
        elif self.required_level == 'appointed' and church_user.role not in ['church_admin', 'church_staff']:
            return False, "임명된 자만 가능합니다."
        
        return True, None


class VolunteerAssignment(models.Model):
    """
    봉사 역할 할당 모델 - MinistryRole을 대체
    """
    church_user = models.ForeignKey(
        'users.ChurchUser',
        on_delete=models.CASCADE,
        related_name='volunteer_assignments',
        verbose_name='교회 사용자'
    )
    volunteer_role = models.ForeignKey(
        VolunteerRole,
        on_delete=models.CASCADE,
        related_name='volunteer_assignments',
        verbose_name='봉사 역할'
    )
    
    # 할당 정보
    assigned_date = models.DateTimeField(auto_now_add=True, verbose_name='할당일')
    start_date = models.DateField(null=True, blank=True, verbose_name='시작일')
    end_date = models.DateField(null=True, blank=True, verbose_name='종료일')
    
    # 권한 커스터마이징
    custom_permissions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='개별 권한',
        help_text='기본 권한에 추가로 부여된 권한들'
    )
    
    # 상태
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    notes = models.TextField(blank=True, verbose_name='비고')
    
    # 승인 관련
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_assignments',
        verbose_name='승인자'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='승인일')
    
    class Meta:
        db_table = 'volunteer_assignments'
        verbose_name = '봉사 할당'
        verbose_name_plural = '봉사 할당들'
        unique_together = [['church_user', 'volunteer_role']]
        ordering = ['-assigned_date']
        indexes = [
            models.Index(fields=['church_user', 'is_active']),
            models.Index(fields=['volunteer_role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.church_user.name} - {self.volunteer_role.name}"
    
    @property
    def all_permissions(self):
        """기본 권한 + 개별 권한 통합"""
        base_permissions = self.volunteer_role.default_permissions or []
        custom_permissions = self.custom_permissions or []
        return list(set(base_permissions + custom_permissions))
    
    def has_permission(self, permission):
        """특정 권한이 있는지 확인"""
        return permission in self.all_permissions
    
    def add_permission(self, permission):
        """권한 추가"""
        if permission not in self.custom_permissions:
            self.custom_permissions.append(permission)
            self.save()
    
    def remove_permission(self, permission):
        """권한 제거"""
        if permission in self.custom_permissions:
            self.custom_permissions.remove(permission)
            self.save()


class VolunteerApplication(models.Model):
    """
    일시적 봉사 신청 모델 (기존 유지)
    """
    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    title = models.CharField(max_length=200, verbose_name='봉사 제목')
    description = models.TextField(verbose_name='설명')
    date = models.DateField(verbose_name='봉사일')
    volunteer_role = models.ForeignKey(
        VolunteerRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='관련 봉사 역할'
    )
    target_roles = models.JSONField(default=list, blank=True, verbose_name='대상 직책 (JSON 배열)')
    max_people = models.PositiveIntegerField(null=True, blank=True, verbose_name='최대 인원')
    applicants = models.ManyToManyField('members.Member', blank=True, verbose_name='신청 교인')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '봉사 신청'
        verbose_name_plural = '봉사 신청'
        ordering = ['-date']

    def __str__(self):
        return self.title


# 기본 봉사 역할 템플릿
DEFAULT_VOLUNTEER_ROLES = [
    # 부서 사역
    {
        'name': '아동부 교사',
        'code': 'children_teacher',
        'category': 'department',
        'description': '아동부 어린이들을 가르치고 돌보는 역할',
        'required_level': 'member',
        'requires_training': True,
        'training_requirements': '아동 교육 기초 과정 이수',
        'default_permissions': [
            'member.view.own_group',
            'member.update.own_group',
            'attendance.view.own_group',
            'attendance.create.own_group',
            'attendance.update.own_group',
            'prayer.view.own_group',
            'prayer.create.own_group',
            'education.view.own_group',
            'education.manage.own_group',
        ]
    },
    {
        'name': '청년부 리더',
        'code': 'youth_leader',
        'category': 'department', 
        'description': '청년부를 이끌고 관리하는 역할',
        'required_level': 'experienced',
        'requires_training': True,
        'training_requirements': '리더십 교육 과정 이수',
        'default_permissions': [
            'member.view.own_group',
            'member.update.own_group',
            'attendance.view.own_group',
            'attendance.create.own_group',
            'attendance.update.own_group',
            'prayer.view.own_group',
            'prayer.create.own_group',
            'group.manage.own_group',
            'announcement.create.own_group',
        ]
    },
    # 예배 사역
    {
        'name': '찬양팀 리더',
        'code': 'worship_leader',
        'category': 'worship',
        'description': '찬양팀을 이끌고 예배 음악을 담당하는 역할',
        'required_level': 'experienced',
        'requires_training': False,
        'default_permissions': [
            'member.view.own_group',
            'attendance.view.own_group',
            'attendance.create.own_group',
            'group.manage.own_group',
        ]
    },
    {
        'name': '찬양팀원',
        'code': 'worship_member',
        'category': 'worship',
        'description': '찬양팀에서 악기나 성가대로 섬기는 역할',
        'required_level': 'member',
        'requires_training': False,
        'default_permissions': [
            'member.view.own',
            'attendance.view.own',
        ]
    },
    # 돌봄 사역
    {
        'name': '셀 리더',
        'code': 'cell_leader',
        'category': 'care',
        'description': '소그룹/셀을 이끌고 돌보는 역할',
        'required_level': 'member',
        'requires_training': True,
        'training_requirements': '셀 리더 교육 과정 이수',
        'default_permissions': [
            'member.view.own_group',
            'attendance.view.own_group',
            'attendance.create.own_group',
            'prayer.view.own_group',
            'prayer.create.own_group',
            'group.manage.own_group',
        ]
    },
    {
        'name': '구역장',
        'code': 'district_leader',
        'category': 'care',
        'description': '구역을 관리하고 심방하는 역할',
        'required_level': 'appointed',
        'requires_training': True,
        'training_requirements': '구역장 교육 과정 이수',
        'default_permissions': [
            'member.view.own_group',
            'attendance.view.own_group',
            'prayer.view.own_group',
            'group.manage.own_group',
            'announcement.create.own_group',
        ]
    },
    # 시설 관리
    {
        'name': '미디어팀',
        'code': 'media_team',
        'category': 'media',
        'description': '영상, 음향, 방송 장비를 관리하는 역할',
        'required_level': 'trained',
        'requires_training': True,
        'training_requirements': '미디어 장비 교육 이수',
        'default_permissions': [
            'member.view.own',
            'attendance.view.own',
        ]
    },
    {
        'name': '주방팀',
        'code': 'kitchen_team',
        'category': 'facility',
        'description': '교회 급식과 다과를 준비하는 역할',
        'required_level': 'anyone',
        'requires_training': False,
        'default_permissions': [
            'member.view.own',
        ]
    },
]