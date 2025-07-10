from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta


class Prayer(models.Model):
    """기도제목 모델"""
    
    class PrayerType(models.TextChoices):
        PERSONAL = 'personal', '개인'
        FAMILY = 'family', '가정'
        CHURCH = 'church', '교회'
        MISSION = 'mission', '선교'
        HEALING = 'healing', '치유'
        THANKSGIVING = 'thanksgiving', '감사'
        GUIDANCE = 'guidance', '인도'
        OTHER = 'other', '기타'
    
    class Priority(models.TextChoices):
        LOW = 'low', '낮음'
        MEDIUM = 'medium', '보통'
        HIGH = 'high', '높음'
        URGENT = 'urgent', '긴급'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', '진행중'
        ANSWERED = 'answered', '응답됨'
        CLOSED = 'closed', '종료됨'
        PRIVATE = 'private', '비공개'
    
    # 기본 정보
    church = models.ForeignKey(
        'church.Church', 
        on_delete=models.CASCADE, 
        related_name='prayers',
        verbose_name='소속 교회'
    )
    member = models.ForeignKey(
        'members.Member', 
        on_delete=models.CASCADE, 
        related_name='prayers',
        verbose_name='교인'
    )
    title = models.CharField(
        max_length=200, 
        verbose_name='제목'
    )
    content = models.TextField(
        verbose_name='기도제목 내용'
    )
    
    # 분류 및 우선순위
    prayer_type = models.CharField(
        max_length=20, 
        choices=PrayerType.choices, 
        default=PrayerType.PERSONAL,
        verbose_name='기도제목 유형'
    )
    priority = models.CharField(
        max_length=20, 
        choices=Priority.choices, 
        default=Priority.MEDIUM,
        verbose_name='우선순위'
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.ACTIVE,
        verbose_name='상태'
    )
    
    # 공개 설정
    is_public = models.BooleanField(
        default=True, 
        verbose_name='공개 여부'
    )
    is_shared_with_leaders = models.BooleanField(
        default=False, 
        verbose_name='리더진 공유'
    )
    
    # 날짜 정보
    prayer_date = models.DateField(
        default=timezone.now, 
        verbose_name='기도 시작일'
    )
    target_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='목표 날짜'
    )
    answered_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='응답 날짜'
    )
    
    # 그룹 정보
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prayers',
        verbose_name='그룹'
    )
    
    # 태그
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='태그',
        help_text='쉼표로 구분하여 입력'
    )
    
    # 메모
    answer_note = models.TextField(
        blank=True,
        verbose_name='응답 메모'
    )
    private_note = models.TextField(
        blank=True,
        verbose_name='비공개 메모'
    )
    
    # 시스템 필드
    created_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_prayers',
        verbose_name='작성자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    # 통계 필드
    prayer_count = models.IntegerField(
        default=0, 
        verbose_name='기도 카운트'
    )
    
    class Meta:
        db_table = 'prayers'
        verbose_name = '기도제목'
        verbose_name_plural = '기도제목들'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['church', 'status']),
            models.Index(fields=['member', 'prayer_date']),
            models.Index(fields=['prayer_type', 'priority']),
        ]

    def __str__(self):
        return f'{self.member.name} - {self.title}'
    
    def clean(self):
        """유효성 검사"""
        if self.member.church != self.church:
            raise ValidationError('교인과 교회가 일치하지 않습니다.')
        
        if self.group and self.group.church != self.church:
            raise ValidationError('그룹과 교회가 일치하지 않습니다.')
        
        if self.target_date and self.target_date < self.prayer_date:
            raise ValidationError('목표 날짜는 기도 시작일 이후여야 합니다.')
        
        if self.answered_date and self.answered_date < self.prayer_date:
            raise ValidationError('응답 날짜는 기도 시작일 이후여야 합니다.')
    
    def save(self, *args, **kwargs):
        # 응답됨 상태일 때 응답 날짜 자동 설정
        if self.status == self.Status.ANSWERED and not self.answered_date:
            self.answered_date = timezone.now().date()
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """목표 날짜 초과 여부"""
        if self.target_date and self.status == self.Status.ACTIVE:
            return date.today() > self.target_date
        return False
    
    @property
    def days_to_target(self):
        """목표 날짜까지 남은 일수"""
        if self.target_date:
            return (self.target_date - date.today()).days
        return None
    
    @property
    def prayer_duration(self):
        """기도 진행 기간"""
        if self.status == self.Status.ANSWERED and self.answered_date:
            return (self.answered_date - self.prayer_date).days
        return (date.today() - self.prayer_date).days
    
    def get_tags_list(self):
        """태그 리스트 반환"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def increment_prayer_count(self):
        """기도 카운트 증가"""
        self.prayer_count += 1
        self.save(update_fields=['prayer_count'])


class PrayerComment(models.Model):
    """기도제목 댓글 모델"""
    
    prayer = models.ForeignKey(
        Prayer,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='기도제목'
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='prayer_comments',
        verbose_name='작성자'
    )
    content = models.TextField(
        verbose_name='댓글 내용'
    )
    is_encouragement = models.BooleanField(
        default=False,
        verbose_name='격려 댓글'
    )
    is_private = models.BooleanField(
        default=False,
        verbose_name='비공개 댓글'
    )
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'prayer_comments'
        verbose_name = '기도제목 댓글'
        verbose_name_plural = '기도제목 댓글들'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.member.name} - {self.content[:30]}...'


class PrayerGroup(models.Model):
    """기도 그룹 모델"""
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='prayer_groups',
        verbose_name='소속 교회'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='그룹명'
    )
    description = models.TextField(
        blank=True,
        verbose_name='설명'
    )
    
    # 멤버 관리
    members = models.ManyToManyField(
        'members.Member',
        through='PrayerGroupMember',
        related_name='prayer_groups',
        verbose_name='멤버들'
    )
    
    # 설정
    is_public = models.BooleanField(
        default=True,
        verbose_name='공개 여부'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성 상태'
    )
    
    # 정기 모임 설정
    meeting_day = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='정기 모임 요일'
    )
    meeting_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='모임 시간'
    )
    
    # 시스템 필드
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_prayer_groups',
        verbose_name='생성자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'prayer_groups'
        verbose_name = '기도 그룹'
        verbose_name_plural = '기도 그룹들'
        ordering = ['name']
    
    def __str__(self):
        return f'{self.church.name} - {self.name}'
    
    @property
    def member_count(self):
        """멤버 수"""
        return self.members.count()


class PrayerGroupMember(models.Model):
    """기도 그룹 멤버 모델"""
    
    class Role(models.TextChoices):
        LEADER = 'leader', '리더'
        MEMBER = 'member', '멤버'
    
    prayer_group = models.ForeignKey(
        PrayerGroup,
        on_delete=models.CASCADE,
        related_name='group_members',
        verbose_name='기도 그룹'
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='prayer_group_memberships',
        verbose_name='멤버'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
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
    
    class Meta:
        db_table = 'prayer_group_members'
        verbose_name = '기도 그룹 멤버'
        verbose_name_plural = '기도 그룹 멤버들'
        unique_together = [['prayer_group', 'member']]
    
    def __str__(self):
        return f'{self.prayer_group.name} - {self.member.name} ({self.get_role_display()})'