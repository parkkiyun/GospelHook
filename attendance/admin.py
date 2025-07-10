from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import Attendance, AttendanceTemplate


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'member_name', 'church_name', 'date', 'worship_type', 
        'status_display', 'group_name', 'arrival_time', 'recorded_by'
    ]
    list_filter = [
        'church', 'status', 'worship_type', 'date', 'group',
        'recorded_by', 'created_at'
    ]
    search_fields = [
        'member__name', 'member__phone', 'church__name', 
        'group__name', 'notes'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'duration_display', 
        'is_present_display', 'church_name'
    ]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'member', 'date', 'worship_type')
        }),
        ('출석 상태', {
            'fields': ('status', 'group', 'notes')
        }),
        ('시간 정보', {
            'fields': ('arrival_time', 'departure_time', 'duration_display'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('recorded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('참조 정보', {
            'fields': ('church_name', 'is_present_display'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'date'
    
    def member_name(self, obj):
        """교인명 표시"""
        return format_html(
            '<a href="/admin/members/member/{}/change/">{}</a>',
            obj.member.id, obj.member.name
        )
    member_name.short_description = '교인명'
    
    def church_name(self, obj):
        """교회명 표시"""
        return obj.church.name
    church_name.short_description = '소속 교회'
    
    def group_name(self, obj):
        """그룹명 표시"""
        if obj.group:
            return format_html(
                '<a href="/admin/groups/group/{}/change/">{}</a>',
                obj.group.id, obj.group.name
            )
        return '-'
    group_name.short_description = '그룹'
    
    def status_display(self, obj):
        """출석 상태 표시"""
        status_colors = {
            'present': 'green',
            'late': 'orange',
            'absent': 'red',
            'early_leave': 'blue',
            'excused': 'purple',
            'sick': 'gray'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = '출석 상태'
    
    def duration_display(self, obj):
        """참석 시간 표시"""
        duration = obj.get_duration()
        if duration:
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            return f"{hours}시간 {minutes}분"
        return '-'
    duration_display.short_description = '참석 시간'
    
    def is_present_display(self, obj):
        """출석 여부 표시"""
        if obj.is_present():
            return format_html('<span style="color: green;">출석</span>')
        return format_html('<span style="color: red;">결석</span>')
    is_present_display.short_description = '출석 여부'
    
    def get_queryset(self, request):
        """쿼리셋 최적화"""
        return super().get_queryset(request).select_related(
            'church', 'member', 'group', 'recorded_by'
        )
    
    def save_model(self, request, obj, form, change):
        """기록자 자동 설정"""
        if not obj.recorded_by:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_present', 'mark_absent', 'mark_late']
    
    def mark_present(self, request, queryset):
        """출석으로 변경"""
        updated = queryset.update(status='present')
        self.message_user(request, f'{updated}개의 출석 기록이 출석으로 변경되었습니다.')
    mark_present.short_description = '선택된 항목을 출석으로 변경'
    
    def mark_absent(self, request, queryset):
        """결석으로 변경"""
        updated = queryset.update(status='absent')
        self.message_user(request, f'{updated}개의 출석 기록이 결석으로 변경되었습니다.')
    mark_absent.short_description = '선택된 항목을 결석으로 변경'
    
    def mark_late(self, request, queryset):
        """지각으로 변경"""
        updated = queryset.update(status='late')
        self.message_user(request, f'{updated}개의 출석 기록이 지각으로 변경되었습니다.')
    mark_late.short_description = '선택된 항목을 지각으로 변경'


@admin.register(AttendanceTemplate)
class AttendanceTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'church', 'worship_type', 'day_of_week_display', 
        'start_time', 'end_time', 'auto_check_enabled', 'is_active'
    ]
    list_filter = [
        'church', 'worship_type', 'day_of_week', 'is_active', 
        'auto_check_enabled', 'created_at'
    ]
    search_fields = [
        'name', 'church__name', 'worship_type'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'next_occurrence_display',
        'target_groups_display'
    ]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'name', 'worship_type')
        }),
        ('일정 설정', {
            'fields': ('day_of_week', 'start_time', 'end_time')
        }),
        ('대상 그룹', {
            'fields': ('target_groups', 'target_groups_display'),
            'classes': ('collapse',)
        }),
        ('자동 체크 설정', {
            'fields': ('auto_check_enabled', 'auto_check_time'),
            'classes': ('collapse',)
        }),
        ('상태 정보', {
            'fields': ('is_active', 'next_occurrence_display'),
            'classes': ('collapse',)
        }),
        ('시스템 필드', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['target_groups']
    
    def day_of_week_display(self, obj):
        """요일 표시"""
        days = ['월', '화', '수', '목', '금', '토', '일']
        return days[obj.day_of_week]
    day_of_week_display.short_description = '요일'
    
    def next_occurrence_display(self, obj):
        """다음 예배 날짜 표시"""
        try:
            next_date = obj.get_next_occurrence()
            return next_date.strftime('%Y-%m-%d')
        except:
            return '-'
    next_occurrence_display.short_description = '다음 예배일'
    
    def target_groups_display(self, obj):
        """대상 그룹 표시"""
        groups = obj.target_groups.all()
        if groups:
            return ', '.join([group.name for group in groups])
        return '전체 교인'
    target_groups_display.short_description = '대상 그룹'
    
    def get_queryset(self, request):
        """쿼리셋 최적화"""
        return super().get_queryset(request).select_related(
            'church', 'created_by'
        ).prefetch_related('target_groups')
    
    def save_model(self, request, obj, form, change):
        """생성자 자동 설정"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['create_attendance_records']
    
    def create_attendance_records(self, request, queryset):
        """출석 기록 생성"""
        total_created = 0
        for template in queryset:
            if template.is_active:
                created = template.create_attendance_records()
                total_created += created
        
        self.message_user(
            request, 
            f'{total_created}개의 출석 기록이 생성되었습니다.'
        )
    create_attendance_records.short_description = '선택된 템플릿으로 출석 기록 생성'