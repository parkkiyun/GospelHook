from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, datetime, timedelta


class Attendance(models.Model):
    """출석 기록 모델"""
    
    class AttendanceStatus(models.TextChoices):
        PRESENT = 'present', '출석'
        ABSENT = 'absent', '결석'
        LATE = 'late', '지각'
        EARLY_LEAVE = 'early_leave', '조퇴'
        EXCUSED = 'excused', '공결'
        SICK = 'sick', '병결'
        
    class WorshipType(models.TextChoices):
        SUNDAY_MORNING = 'sunday_morning', '주일 1부'
        SUNDAY_EVENING = 'sunday_evening', '주일 2부'
        WEDNESDAY = 'wednesday', '수요예배'
        FRIDAY = 'friday', '금요철야'
        DAWN = 'dawn', '새벽예배'
        SPECIAL = 'special', '특별집회'
        CELL_GROUP = 'cell_group', '셀모임'
        BIBLE_STUDY = 'bible_study', '성경공부'
        YOUTH = 'youth', '청년예배'
        CHILDREN = 'children', '어린이예배'
        ETC = 'etc', '기타'
    
    # 기본 정보
    church = models.ForeignKey(
        'church.Church', 
        on_delete=models.CASCADE, 
        related_name='attendances',
        verbose_name='소속 교회'
    )
    member = models.ForeignKey(
        'members.Member', 
        on_delete=models.CASCADE, 
        related_name='attendances',
        verbose_name='교인'
    )
    date = models.DateField(verbose_name='날짜')
    status = models.CharField(
        max_length=20, 
        choices=AttendanceStatus.choices, 
        default=AttendanceStatus.PRESENT,
        verbose_name='출석 상태'
    )
    worship_type = models.CharField(
        max_length=20, 
        choices=WorshipType.choices, 
        verbose_name='예배 종류'
    )
    
    # 그룹 정보 (선택적)
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances',
        verbose_name='그룹'
    )
    
    # 메모 및 추가 정보
    notes = models.TextField(blank=True, verbose_name='메모')
    arrival_time = models.TimeField(
        null=True, 
        blank=True, 
        verbose_name='도착 시간'
    )
    departure_time = models.TimeField(
        null=True, 
        blank=True, 
        verbose_name='출발 시간'
    )
    
    # 시스템 필드
    recorded_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recorded_attendances',
        verbose_name='기록자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        db_table = 'attendance'
        verbose_name = '출석'
        verbose_name_plural = '출석들'
        unique_together = [['member', 'date', 'worship_type']]
        ordering = ['-date', 'worship_type', 'member__name']
        indexes = [
            models.Index(fields=['church', 'date']),
            models.Index(fields=['member', 'date']),
            models.Index(fields=['worship_type', 'date']),
        ]

    def __str__(self):
        return f'{self.member.name} - {self.date} - {self.get_worship_type_display()} ({self.get_status_display()})'
    
    def clean(self):
        """유효성 검사"""
        # 미래 날짜 출석 기록 방지
        if self.date > date.today():
            raise ValidationError('미래 날짜의 출석은 기록할 수 없습니다.')
        
        # 같은 교회 소속인지 확인
        if self.member.church != self.church:
            raise ValidationError('교인과 교회가 일치하지 않습니다.')
        
        # 그룹이 지정된 경우 같은 교회 소속인지 확인
        if self.group and self.group.church != self.church:
            raise ValidationError('그룹과 교회가 일치하지 않습니다.')
    
    def is_present(self):
        """출석 여부 확인"""
        return self.status in [self.AttendanceStatus.PRESENT, self.AttendanceStatus.LATE]
    
    def is_absent(self):
        """결석 여부 확인"""
        return self.status in [self.AttendanceStatus.ABSENT]
    
    def get_duration(self):
        """예배 참석 시간 계산"""
        if self.arrival_time and self.departure_time:
            arrival = datetime.combine(self.date, self.arrival_time)
            departure = datetime.combine(self.date, self.departure_time)
            return departure - arrival
        return None


class AttendanceTemplate(models.Model):
    """출석 템플릿 모델 (정기 예배 설정)"""
    
    church = models.ForeignKey(
        'church.Church', 
        on_delete=models.CASCADE, 
        related_name='attendance_templates',
        verbose_name='소속 교회'
    )
    name = models.CharField(max_length=100, verbose_name='템플릿명')
    worship_type = models.CharField(
        max_length=20, 
        choices=Attendance.WorshipType.choices, 
        verbose_name='예배 종류'
    )
    
    # 정기 예배 설정
    day_of_week = models.IntegerField(
        choices=[
            (0, '월요일'), (1, '화요일'), (2, '수요일'), (3, '목요일'),
            (4, '금요일'), (5, '토요일'), (6, '일요일')
        ],
        verbose_name='요일'
    )
    start_time = models.TimeField(verbose_name='시작 시간')
    end_time = models.TimeField(verbose_name='종료 시간')
    
    # 그룹 설정
    target_groups = models.ManyToManyField(
        'groups.Group',
        blank=True,
        related_name='attendance_templates',
        verbose_name='대상 그룹'
    )
    
    # 활성 상태
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    
    # 자동 출석 체크 설정
    auto_check_enabled = models.BooleanField(
        default=False, 
        verbose_name='자동 출석 체크 활성화'
    )
    auto_check_time = models.TimeField(
        null=True, 
        blank=True, 
        verbose_name='자동 출석 체크 시간'
    )
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    created_by = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_attendance_templates',
        verbose_name='생성자'
    )
    
    class Meta:
        db_table = 'attendance_templates'
        verbose_name = '출석 템플릿'
        verbose_name_plural = '출석 템플릿들'
        unique_together = [['church', 'name']]
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f'{self.church.name} - {self.name} ({self.get_day_of_week_display()})'
    
    def get_next_occurrence(self):
        """다음 예배 날짜 계산"""
        today = date.today()
        days_ahead = self.day_of_week - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    
    def create_attendance_records(self, target_date=None):
        """출석 기록 생성"""
        if not target_date:
            target_date = self.get_next_occurrence()
        
        # 대상 그룹의 멤버들 조회
        if self.target_groups.exists():
            from groups.models import GroupMember
            members = []
            for group in self.target_groups.all():
                group_members = GroupMember.objects.filter(
                    group=group,
                    is_active=True
                ).select_related('member')
                members.extend([gm.member for gm in group_members])
        else:
            # 전체 교인 대상
            from members.models import Member
            members = Member.objects.filter(
                church=self.church,
                is_active=True,
                status='active'
            )
        
        # 출석 기록 생성
        created_count = 0
        for member in members:
            attendance, created = Attendance.objects.get_or_create(
                church=self.church,
                member=member,
                date=target_date,
                worship_type=self.worship_type,
                defaults={
                    'status': Attendance.AttendanceStatus.ABSENT,
                    'notes': f'{self.name} 자동 생성'
                }
            )
            if created:
                created_count += 1
        
        return created_count