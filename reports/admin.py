from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from .models import (
    ReportTemplate, Report, Dashboard, StatisticsSummary,
    ReportSchedule, ExportLog, MinistryReport, 
    MinistryReportTemplate, MinistryReportComment
)


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'church', 'report_type', 'is_auto_generate', 
        'generate_frequency', 'last_generated', 'is_active'
    ]
    list_filter = ['church', 'report_type', 'is_auto_generate', 'generate_frequency', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['last_generated', 'created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'name', 'description', 'report_type')
        }),
        ('설정', {
            'fields': ('config',)
        }),
        ('자동 생성', {
            'fields': ('is_auto_generate', 'generate_frequency', 'last_generated')
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'template', 'status', 'start_date', 'end_date',
        'generated_at', 'completed_at', 'has_pdf', 'has_excel'
    ]
    list_filter = ['status', 'generated_at', 'template__report_type', 'church']
    search_fields = ['title', 'summary', 'template__name']
    readonly_fields = ['generated_at', 'completed_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'template', 'title', 'start_date', 'end_date')
        }),
        ('데이터', {
            'fields': ('data', 'summary')
        }),
        ('상태', {
            'fields': ('status', 'error_message')
        }),
        ('파일', {
            'fields': ('pdf_file', 'excel_file')
        }),
        ('시스템 정보', {
            'fields': ('generated_by', 'generated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_pdf(self, obj):
        return bool(obj.pdf_file)
    has_pdf.boolean = True
    has_pdf.short_description = 'PDF'
    
    def has_excel(self, obj):
        return bool(obj.excel_file)
    has_excel.boolean = True
    has_excel.short_description = 'Excel'


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'church', 'is_public', 'auto_refresh', 
        'refresh_interval', 'is_active', 'created_at'
    ]
    list_filter = ['church', 'is_public', 'auto_refresh', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'name', 'description')
        }),
        ('레이아웃', {
            'fields': ('layout', 'widgets')
        }),
        ('권한', {
            'fields': ('is_public', 'allowed_roles')
        }),
        ('새로고침', {
            'fields': ('auto_refresh', 'refresh_interval')
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StatisticsSummary)
class StatisticsSummaryAdmin(admin.ModelAdmin):
    list_display = [
        'church', 'date', 'total_members', 'active_members',
        'sunday_attendance', 'attendance_rate', 'total_prayers'
    ]
    list_filter = ['church', 'date']
    search_fields = ['church__name']
    readonly_fields = ['calculated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'date')
        }),
        ('교인 통계', {
            'fields': (
                'total_members', 'active_members',
                'new_members_today', 'new_members_this_month'
            )
        }),
        ('출석 통계', {
            'fields': (
                'sunday_attendance', 'wednesday_attendance',
                'total_attendance_this_week', 'attendance_rate'
            )
        }),
        ('그룹 통계', {
            'fields': ('total_groups', 'active_groups')
        }),
        ('기도 통계', {
            'fields': (
                'total_prayers', 'active_prayers', 'answered_prayers_today'
            )
        }),
        ('재정 통계', {
            'fields': ('total_offerings_today', 'total_offerings_this_month')
        }),
        ('시스템 정보', {
            'fields': ('calculated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'template', 'cron_expression', 'next_run', 'last_run',
        'is_running', 'last_success', 'error_count', 'is_active'
    ]
    list_filter = ['is_active', 'is_running', 'last_success']
    search_fields = ['template__name', 'notification_emails']
    readonly_fields = ['last_run', 'is_running', 'last_success', 'error_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('스케줄 정보', {
            'fields': ('template', 'cron_expression', 'next_run', 'last_run')
        }),
        ('실행 상태', {
            'fields': ('is_running', 'last_success', 'error_count')
        }),
        ('알림 설정', {
            'fields': (
                'notify_on_success', 'notify_on_failure', 'notification_emails'
            )
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    list_display = [
        'church', 'export_type', 'status', 'record_count',
        'file_size_display', 'requested_by', 'requested_at', 'expires_at'
    ]
    list_filter = ['export_type', 'status', 'requested_at', 'church']
    search_fields = ['church__name', 'requested_by__username', 'error_message']
    readonly_fields = ['requested_at', 'completed_at', 'expires_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'export_type', 'status')
        }),
        ('필터', {
            'fields': ('filters',)
        }),
        ('결과', {
            'fields': ('file_path', 'file_size', 'record_count')
        }),
        ('오류', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('requested_by', 'requested_at', 'completed_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size > 0:
            if obj.file_size < 1024:
                return f"{obj.file_size} bytes"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"
    file_size_display.short_description = '파일 크기'


# Ministry Report 관련 Inline
class MinistryReportCommentInline(admin.TabularInline):
    model = MinistryReportComment
    fields = ['author', 'comment_type', 'content', 'parent', 'created_at']
    readonly_fields = ['created_at']
    extra = 0
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False).select_related('author')


@admin.register(MinistryReport)
class MinistryReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'reporter', 'church', 'category', 'status', 'priority',
        'report_date', 'attendance_count', 'budget_used', 'attachment_count',
        'days_since_report', 'created_at'
    ]
    list_filter = [
        'church', 'category', 'status', 'priority', 'report_date',
        'department', 'volunteer_role', 'created_at'
    ]
    search_fields = [
        'title', 'summary', 'content', 'reporter__name', 
        'department__name', 'volunteer_role__name'
    ]
    readonly_fields = [
        'days_since_report', 'attachment_count', 'is_editable',
        'created_at', 'updated_at', 'submitted_at', 'reviewed_at'
    ]
    inlines = [MinistryReportCommentInline]
    
    fieldsets = (
        ('기본 정보', {
            'fields': (
                'church', 'title', 'category', 'priority', 'report_date',
                'start_date', 'end_date'
            )
        }),
        ('담당자 정보', {
            'fields': ('reporter', 'department', 'volunteer_role')
        }),
        ('보고서 내용', {
            'fields': (
                'summary', 'content', 'achievements', 'challenges',
                'next_plans', 'prayer_requests'
            )
        }),
        ('수치 데이터', {
            'fields': (
                'attendance_count', 'new_members_count',
                'budget_used', 'budget_remaining'
            ),
            'classes': ('collapse',)
        }),
        ('추가 정보', {
            'fields': ('custom_data', 'attachments', 'tags'),
            'classes': ('collapse',)
        }),
        ('상태 관리', {
            'fields': ('status', 'is_public')
        }),
        ('검토 정보', {
            'fields': ('reviewer', 'reviewed_at', 'review_comments'),
            'classes': ('collapse',)
        }),
        ('통계 정보', {
            'fields': ('days_since_report', 'attachment_count', 'is_editable'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at', 'submitted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def attachment_count(self, obj):
        return obj.get_attachment_count()
    attachment_count.short_description = '첨부파일 수'
    
    def days_since_report(self, obj):
        days = obj.days_since_report
        if days == 0:
            return "오늘"
        elif days == 1:
            return "어제"
        elif days < 7:
            return f"{days}일 전"
        elif days < 30:
            return f"{days // 7}주 전"
        else:
            return f"{days // 30}개월 전"
    days_since_report.short_description = '경과 시간'
    
    def get_status_display_colored(self, obj):
        colors = {
            'draft': '#6c757d',
            'submitted': '#17a2b8', 
            'reviewed': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'archived': '#6f42c1'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_display_colored.short_description = '상태'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'church', 'reporter', 'department', 'volunteer_role', 'reviewer'
        ).prefetch_related('comments')

    actions = ['mark_as_approved', 'mark_as_archived']
    
    def mark_as_approved(self, request, queryset):
        updated = 0
        for report in queryset:
            if report.status in ['submitted', 'reviewed']:
                report.approve(request.user.church_user, "관리자 승인")
                updated += 1
        self.message_user(request, f'{updated}개 보고서가 승인되었습니다.')
    mark_as_approved.short_description = '선택된 보고서 승인'
    
    def mark_as_archived(self, request, queryset):
        updated = queryset.filter(status='approved').update(status='archived')
        self.message_user(request, f'{updated}개 보고서가 보관되었습니다.')
    mark_as_archived.short_description = '선택된 보고서 보관'


@admin.register(MinistryReportTemplate)
class MinistryReportTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'church', 'category', 'auto_create', 'auto_create_schedule',
        'requires_approval', 'is_active', 'created_at'
    ]
    list_filter = [
        'church', 'category', 'auto_create', 'auto_create_schedule',
        'requires_approval', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description', 'church__name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['target_roles', 'target_groups', 'default_reviewers']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'name', 'description', 'category')
        }),
        ('템플릿 설정', {
            'fields': ('fields_config', 'required_fields')
        }),
        ('자동 생성', {
            'fields': ('auto_create', 'auto_create_schedule'),
            'classes': ('collapse',)
        }),
        ('적용 대상', {
            'fields': ('target_roles', 'target_groups'),
            'classes': ('collapse',)
        }),
        ('승인 프로세스', {
            'fields': ('requires_approval', 'default_reviewers'),
            'classes': ('collapse',)
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'church', 'created_by'
        ).prefetch_related('target_roles', 'target_groups', 'default_reviewers')


@admin.register(MinistryReportComment)
class MinistryReportCommentAdmin(admin.ModelAdmin):
    list_display = [
        'report_link', 'author', 'comment_type', 'content_preview',
        'parent', 'created_at', 'is_deleted'
    ]
    list_filter = [
        'comment_type', 'created_at', 'is_deleted',
        'report__church', 'report__category'
    ]
    search_fields = [
        'content', 'author__name', 'report__title'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('댓글 정보', {
            'fields': ('report', 'author', 'comment_type', 'content')
        }),
        ('관계', {
            'fields': ('parent',)
        }),
        ('상태', {
            'fields': ('is_deleted',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def report_link(self, obj):
        url = reverse('admin:reports_ministryreport_change', args=[obj.report.pk])
        return format_html('<a href="{}">{}</a>', url, obj.report.title)
    report_link.short_description = '보고서'
    
    def content_preview(self, obj):
        if len(obj.content) > 50:
            return obj.content[:50] + '...'
        return obj.content
    content_preview.short_description = '내용 미리보기'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'report', 'author', 'parent'
        )
