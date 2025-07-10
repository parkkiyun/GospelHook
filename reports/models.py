from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta
import json


class ReportTemplate(models.Model):
    """리포트 템플릿 모델"""
    
    class ReportType(models.TextChoices):
        ATTENDANCE = 'attendance', '출석 통계'
        MEMBER = 'member', '교인 통계'
        FINANCIAL = 'financial', '재정 통계'
        GROWTH = 'growth', '성장 통계'
        PRAYER = 'prayer', '기도제목 통계'
        EDUCATION = 'education', '교육 통계'
        GROUP = 'group', '그룹 통계'
        CUSTOM = 'custom', '사용자 정의'
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='report_templates',
        verbose_name='교회'
    )
    name = models.CharField(max_length=200, verbose_name='템플릿명')
    description = models.TextField(blank=True, verbose_name='설명')
    report_type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        verbose_name='리포트 유형'
    )
    
    # 리포트 설정
    config = models.JSONField(
        default=dict,
        verbose_name='설정',
        help_text='리포트 생성에 필요한 설정 정보'
    )
    
    # 자동 생성 설정
    is_auto_generate = models.BooleanField(
        default=False,
        verbose_name='자동 생성'
    )
    generate_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', '일별'),
            ('weekly', '주별'),
            ('monthly', '월별'),
            ('quarterly', '분기별'),
            ('yearly', '연별')
        ],
        null=True,
        blank=True,
        verbose_name='생성 주기'
    )
    last_generated = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='마지막 생성 시간'
    )
    
    # 시스템 필드
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_templates',
        verbose_name='생성자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'report_templates'
        verbose_name = '리포트 템플릿'
        verbose_name_plural = '리포트 템플릿들'
        unique_together = [['church', 'name']]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.church.name} - {self.name}"


class Report(models.Model):
    """생성된 리포트 모델"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', '대기중'
        GENERATING = 'generating', '생성중'
        COMPLETED = 'completed', '완료'
        FAILED = 'failed', '실패'
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='교회'
    )
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='generated_reports',
        verbose_name='템플릿'
    )
    title = models.CharField(max_length=200, verbose_name='제목')
    
    # 리포트 기간
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(verbose_name='종료일')
    
    # 리포트 데이터
    data = models.JSONField(
        default=dict,
        verbose_name='리포트 데이터'
    )
    summary = models.TextField(blank=True, verbose_name='요약')
    
    # 생성 정보
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='상태'
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='오류 메시지'
    )
    
    # 파일 첨부
    pdf_file = models.FileField(
        upload_to='reports/pdf/',
        null=True,
        blank=True,
        verbose_name='PDF 파일'
    )
    excel_file = models.FileField(
        upload_to='reports/excel/',
        null=True,
        blank=True,
        verbose_name='Excel 파일'
    )
    
    # 시스템 필드
    generated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name='생성자'
    )
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='완료일'
    )
    
    class Meta:
        db_table = 'reports'
        verbose_name = '리포트'
        verbose_name_plural = '리포트들'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['church', 'status']),
            models.Index(fields=['template', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.start_date} ~ {self.end_date})"
    
    def mark_completed(self):
        """리포트 완료 처리"""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_failed(self, error_message):
        """리포트 실패 처리"""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])


class Dashboard(models.Model):
    """대시보드 모델"""
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='dashboards',
        verbose_name='교회'
    )
    name = models.CharField(max_length=200, verbose_name='대시보드명')
    description = models.TextField(blank=True, verbose_name='설명')
    
    # 대시보드 설정
    layout = models.JSONField(
        default=dict,
        verbose_name='레이아웃 설정',
        help_text='위젯 배치 및 크기 정보'
    )
    widgets = models.JSONField(
        default=list,
        verbose_name='위젯 목록',
        help_text='대시보드에 포함될 위젯들'
    )
    
    # 권한 설정
    is_public = models.BooleanField(
        default=False,
        verbose_name='공개 여부'
    )
    allowed_roles = models.JSONField(
        default=list,
        verbose_name='허용 역할',
        help_text='대시보드 접근 가능한 역할 목록'
    )
    
    # 자동 새로고침
    auto_refresh = models.BooleanField(
        default=True,
        verbose_name='자동 새로고침'
    )
    refresh_interval = models.IntegerField(
        default=300,
        verbose_name='새로고침 간격(초)'
    )
    
    # 시스템 필드
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_dashboards',
        verbose_name='생성자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'dashboards'
        verbose_name = '대시보드'
        verbose_name_plural = '대시보드들'
        unique_together = [['church', 'name']]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.church.name} - {self.name}"


class StatisticsSummary(models.Model):
    """통계 요약 모델 (일별 집계)"""
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='statistics_summaries',
        verbose_name='교회'
    )
    date = models.DateField(verbose_name='날짜')
    
    # 교인 통계
    total_members = models.IntegerField(default=0, verbose_name='총 교인 수')
    active_members = models.IntegerField(default=0, verbose_name='활성 교인 수')
    new_members_today = models.IntegerField(default=0, verbose_name='오늘 신규 교인')
    new_members_this_month = models.IntegerField(default=0, verbose_name='이번 달 신규 교인')
    
    # 출석 통계
    sunday_attendance = models.IntegerField(default=0, verbose_name='주일 출석')
    wednesday_attendance = models.IntegerField(default=0, verbose_name='수요 출석')
    total_attendance_this_week = models.IntegerField(default=0, verbose_name='주간 총 출석')
    attendance_rate = models.FloatField(default=0.0, verbose_name='출석률(%)')
    
    # 그룹 통계
    total_groups = models.IntegerField(default=0, verbose_name='총 그룹 수')
    active_groups = models.IntegerField(default=0, verbose_name='활성 그룹 수')
    
    # 기도제목 통계
    total_prayers = models.IntegerField(default=0, verbose_name='총 기도제목')
    active_prayers = models.IntegerField(default=0, verbose_name='진행중 기도제목')
    answered_prayers_today = models.IntegerField(default=0, verbose_name='오늘 응답된 기도제목')
    
    # 재정 통계 (헌금)
    total_offerings_today = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='오늘 헌금'
    )
    total_offerings_this_month = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='이번 달 헌금'
    )
    
    # 시스템 필드
    calculated_at = models.DateTimeField(auto_now=True, verbose_name='계산일시')
    
    class Meta:
        db_table = 'statistics_summaries'
        verbose_name = '통계 요약'
        verbose_name_plural = '통계 요약들'
        unique_together = [['church', 'date']]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['church', 'date']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.date} 통계"


class ReportSchedule(models.Model):
    """리포트 스케줄 모델"""
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='템플릿'
    )
    
    # 스케줄 설정
    cron_expression = models.CharField(
        max_length=100,
        verbose_name='Cron 표현식',
        help_text='리포트 생성 스케줄 (예: 0 9 * * 1 = 매주 월요일 9시)'
    )
    next_run = models.DateTimeField(
        verbose_name='다음 실행 시간'
    )
    last_run = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='마지막 실행 시간'
    )
    
    # 실행 결과
    is_running = models.BooleanField(
        default=False,
        verbose_name='실행중'
    )
    last_success = models.BooleanField(
        default=True,
        verbose_name='마지막 실행 성공'
    )
    error_count = models.IntegerField(
        default=0,
        verbose_name='연속 실패 횟수'
    )
    
    # 알림 설정
    notify_on_success = models.BooleanField(
        default=False,
        verbose_name='성공시 알림'
    )
    notify_on_failure = models.BooleanField(
        default=True,
        verbose_name='실패시 알림'
    )
    notification_emails = models.TextField(
        blank=True,
        verbose_name='알림 이메일',
        help_text='쉼표로 구분된 이메일 주소'
    )
    
    # 시스템 필드
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'report_schedules'
        verbose_name = '리포트 스케줄'
        verbose_name_plural = '리포트 스케줄들'
        ordering = ['next_run']
    
    def __str__(self):
        return f"{self.template.name} - {self.cron_expression}"
    
    def get_notification_emails_list(self):
        """알림 이메일 리스트 반환"""
        if self.notification_emails:
            return [email.strip() for email in self.notification_emails.split(',')]
        return []


class ExportLog(models.Model):
    """데이터 내보내기 로그 모델"""
    
    class ExportType(models.TextChoices):
        MEMBER = 'member', '교인 데이터'
        ATTENDANCE = 'attendance', '출석 데이터'
        FINANCIAL = 'financial', '재정 데이터'
        PRAYER = 'prayer', '기도제목 데이터'
        FULL_BACKUP = 'full_backup', '전체 백업'
    
    class Status(models.TextChoices):
        PENDING = 'pending', '대기중'
        PROCESSING = 'processing', '처리중'
        COMPLETED = 'completed', '완료'
        FAILED = 'failed', '실패'
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='export_logs',
        verbose_name='교회'
    )
    export_type = models.CharField(
        max_length=20,
        choices=ExportType.choices,
        verbose_name='내보내기 유형'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='상태'
    )
    
    # 필터 조건
    filters = models.JSONField(
        default=dict,
        verbose_name='필터 조건'
    )
    
    # 결과 파일
    file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='파일 경로'
    )
    file_size = models.BigIntegerField(
        default=0,
        verbose_name='파일 크기(bytes)'
    )
    record_count = models.IntegerField(
        default=0,
        verbose_name='레코드 수'
    )
    
    # 오류 정보
    error_message = models.TextField(
        blank=True,
        verbose_name='오류 메시지'
    )
    
    # 시스템 필드
    requested_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='export_logs',
        verbose_name='요청자'
    )
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name='요청일시')
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='완료일시'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='만료일시'
    )
    
    class Meta:
        db_table = 'export_logs'
        verbose_name = '내보내기 로그'
        verbose_name_plural = '내보내기 로그들'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['church', 'status']),
            models.Index(fields=['requested_by', 'status']),
        ]
    
    def __str__(self):
        return f"{self.church.name} - {self.get_export_type_display()} ({self.requested_at})"
    
    def mark_completed(self, file_path, file_size, record_count):
        """내보내기 완료 처리"""
        self.status = self.Status.COMPLETED
        self.file_path = file_path
        self.file_size = file_size
        self.record_count = record_count
        self.completed_at = timezone.now()
        # 7일 후 만료
        self.expires_at = timezone.now() + timedelta(days=7)
        self.save()
    
    def mark_failed(self, error_message):
        """내보내기 실패 처리"""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.save()


class MinistryReport(models.Model):
    """사역 보고서 모델"""
    
    class ReportCategory(models.TextChoices):
        WEEKLY = 'weekly', '주간 보고서'
        MONTHLY = 'monthly', '월간 보고서'
        EVENT = 'event', '행사 보고서'
        PROJECT = 'project', '프로젝트 보고서'
        ACTIVITY = 'activity', '활동 보고서'
        FINANCIAL = 'financial', '재정 보고서'
        ATTENDANCE = 'attendance', '출석 보고서'
        EDUCATION = 'education', '교육 보고서'
        EVANGELISM = 'evangelism', '전도 보고서'
        OTHER = 'other', '기타'
    
    class Status(models.TextChoices):
        DRAFT = 'draft', '임시저장'
        SUBMITTED = 'submitted', '제출됨'
        REVIEWED = 'reviewed', '검토됨'
        APPROVED = 'approved', '승인됨'
        REJECTED = 'rejected', '반려됨'
        ARCHIVED = 'archived', '보관됨'
    
    class Priority(models.TextChoices):
        LOW = 'low', '낮음'
        NORMAL = 'normal', '보통'
        HIGH = 'high', '높음'
        URGENT = 'urgent', '긴급'
    
    # 기본 정보
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='ministry_reports',
        verbose_name='교회'
    )
    title = models.CharField(max_length=200, verbose_name='제목')
    category = models.CharField(
        max_length=20,
        choices=ReportCategory.choices,
        default=ReportCategory.WEEKLY,
        verbose_name='카테고리'
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
        verbose_name='중요도'
    )
    
    # 보고 기간
    report_date = models.DateField(verbose_name='보고 날짜')
    start_date = models.DateField(null=True, blank=True, verbose_name='시작일')
    end_date = models.DateField(null=True, blank=True, verbose_name='종료일')
    
    # 사역자 정보
    reporter = models.ForeignKey(
        'users.ChurchUser',
        on_delete=models.CASCADE,
        related_name='ministry_reports',
        verbose_name='보고자'
    )
    department = models.ForeignKey(
        'groups.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ministry_reports',
        verbose_name='담당 부서/그룹'
    )
    volunteer_role = models.ForeignKey(
        'volunteering.VolunteerRole',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ministry_reports',
        verbose_name='봉사 역할'
    )
    
    # 보고서 내용
    summary = models.TextField(verbose_name='요약')
    content = models.TextField(verbose_name='상세 내용')
    achievements = models.TextField(
        blank=True,
        verbose_name='성과 및 성취',
        help_text='이번 기간 동안의 주요 성과나 성취 사항'
    )
    challenges = models.TextField(
        blank=True,
        verbose_name='어려움 및 과제',
        help_text='직면한 어려움이나 해결해야 할 과제'
    )
    next_plans = models.TextField(
        blank=True,
        verbose_name='향후 계획',
        help_text='다음 기간의 계획이나 목표'
    )
    prayer_requests = models.TextField(
        blank=True,
        verbose_name='기도 제목',
        help_text='사역과 관련된 기도 제목'
    )
    
    # 수치 데이터
    attendance_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='참석 인원'
    )
    new_members_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='신규 인원'
    )
    budget_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='사용 예산'
    )
    budget_remaining = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='잔여 예산'
    )
    
    # 추가 데이터 (JSON)
    custom_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='추가 데이터',
        help_text='커스터마이징된 필드 데이터'
    )
    
    # 첨부 파일
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name='첨부 파일',
        help_text='파일 경로와 정보가 저장되는 JSON 필드'
    )
    
    # 상태 관리
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='상태'
    )
    
    # 검토 정보
    reviewer = models.ForeignKey(
        'users.ChurchUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_ministry_reports',
        verbose_name='검토자'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='검토일시'
    )
    review_comments = models.TextField(
        blank=True,
        verbose_name='검토 의견'
    )
    
    # 태그 및 분류
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name='태그',
        help_text='보고서 분류를 위한 태그'
    )
    
    # 공개 설정
    is_public = models.BooleanField(
        default=False,
        verbose_name='공개 여부',
        help_text='교회 내 다른 사역자들에게 공개할지 여부'
    )
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='제출일시'
    )
    
    class Meta:
        db_table = 'ministry_reports'
        verbose_name = '사역 보고서'
        verbose_name_plural = '사역 보고서들'
        ordering = ['-report_date', '-created_at']
        indexes = [
            models.Index(fields=['church', 'status']),
            models.Index(fields=['reporter', 'status']),
            models.Index(fields=['department', 'report_date']),
            models.Index(fields=['category', 'report_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.reporter.name} ({self.report_date})"
    
    def submit(self):
        """보고서 제출"""
        if self.status == self.Status.DRAFT:
            self.status = self.Status.SUBMITTED
            self.submitted_at = timezone.now()
            self.save(update_fields=['status', 'submitted_at'])
    
    def approve(self, reviewer, comments=''):
        """보고서 승인"""
        self.status = self.Status.APPROVED
        self.reviewer = reviewer
        self.reviewed_at = timezone.now()
        self.review_comments = comments
        self.save(update_fields=['status', 'reviewer', 'reviewed_at', 'review_comments'])
    
    def reject(self, reviewer, comments):
        """보고서 반려"""
        self.status = self.Status.REJECTED
        self.reviewer = reviewer
        self.reviewed_at = timezone.now()
        self.review_comments = comments
        self.save(update_fields=['status', 'reviewer', 'reviewed_at', 'review_comments'])
    
    def archive(self):
        """보고서 보관"""
        self.status = self.Status.ARCHIVED
        self.save(update_fields=['status'])
    
    @property
    def is_editable(self):
        """수정 가능 여부"""
        return self.status in [self.Status.DRAFT, self.Status.REJECTED]
    
    @property
    def days_since_report(self):
        """보고일로부터 경과 일수"""
        return (timezone.now().date() - self.report_date).days
    
    def get_attachment_count(self):
        """첨부 파일 수"""
        return len(self.attachments) if self.attachments else 0


class MinistryReportTemplate(models.Model):
    """사역 보고서 템플릿 모델"""
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='ministry_report_templates',
        verbose_name='교회'
    )
    name = models.CharField(max_length=100, verbose_name='템플릿명')
    description = models.TextField(blank=True, verbose_name='설명')
    category = models.CharField(
        max_length=20,
        choices=MinistryReport.ReportCategory.choices,
        verbose_name='카테고리'
    )
    
    # 템플릿 설정
    fields_config = models.JSONField(
        default=dict,
        verbose_name='필드 설정',
        help_text='보고서에 포함될 필드들의 설정'
    )
    required_fields = models.JSONField(
        default=list,
        verbose_name='필수 필드',
        help_text='반드시 입력해야 하는 필드 목록'
    )
    
    # 자동 생성 설정
    auto_create = models.BooleanField(
        default=False,
        verbose_name='자동 생성',
        help_text='주기적으로 자동으로 보고서 생성'
    )
    auto_create_schedule = models.CharField(
        max_length=20,
        choices=[
            ('weekly', '주간'),
            ('monthly', '월간'),
            ('quarterly', '분기'),
        ],
        null=True,
        blank=True,
        verbose_name='자동 생성 주기'
    )
    
    # 적용 대상
    target_roles = models.ManyToManyField(
        'volunteering.VolunteerRole',
        blank=True,
        verbose_name='적용 봉사 역할',
        help_text='이 템플릿을 사용할 봉사 역할들'
    )
    target_groups = models.ManyToManyField(
        'groups.Group',
        blank=True,
        verbose_name='적용 그룹',
        help_text='이 템플릿을 사용할 그룹들'
    )
    
    # 승인 프로세스
    requires_approval = models.BooleanField(
        default=True,
        verbose_name='승인 필요',
        help_text='이 템플릿으로 작성된 보고서가 승인을 거쳐야 하는지'
    )
    default_reviewers = models.ManyToManyField(
        'users.ChurchUser',
        blank=True,
        verbose_name='기본 검토자',
        help_text='이 템플릿으로 작성된 보고서의 기본 검토자들'
    )
    
    # 시스템 필드
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    created_by = models.ForeignKey(
        'users.ChurchUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ministry_report_templates',
        verbose_name='생성자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'ministry_report_templates'
        verbose_name = '사역 보고서 템플릿'
        verbose_name_plural = '사역 보고서 템플릿들'
        unique_together = [['church', 'name']]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.church.name} - {self.name}"
    
    def create_report_for_user(self, church_user, report_date=None):
        """사용자를 위한 보고서 생성"""
        if not report_date:
            report_date = timezone.now().date()
        
        # 기본 데이터로 보고서 생성
        report = MinistryReport.objects.create(
            church=self.church,
            title=f"{self.name} - {report_date}",
            category=self.category,
            report_date=report_date,
            reporter=church_user,
            custom_data=self.fields_config
        )
        
        return report


class MinistryReportComment(models.Model):
    """사역 보고서 댓글 모델"""
    
    report = models.ForeignKey(
        MinistryReport,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='보고서'
    )
    author = models.ForeignKey(
        'users.ChurchUser',
        on_delete=models.CASCADE,
        verbose_name='작성자'
    )
    content = models.TextField(verbose_name='내용')
    
    # 댓글 유형
    comment_type = models.CharField(
        max_length=20,
        choices=[
            ('comment', '일반 댓글'),
            ('suggestion', '제안'),
            ('question', '질문'),
            ('approval', '승인 의견'),
        ],
        default='comment',
        verbose_name='댓글 유형'
    )
    
    # 부모 댓글 (대댓글 기능)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='부모 댓글'
    )
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    is_deleted = models.BooleanField(default=False, verbose_name='삭제됨')
    
    class Meta:
        db_table = 'ministry_report_comments'
        verbose_name = '사역 보고서 댓글'
        verbose_name_plural = '사역 보고서 댓글들'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.report.title} - {self.author.name} 댓글"