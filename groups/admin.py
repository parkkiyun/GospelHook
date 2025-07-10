from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Group, GroupMember


class GroupMemberInline(admin.TabularInline):
    """그룹 멤버 인라인 어드민"""
    model = GroupMember
    extra = 1
    fields = ['member', 'role', 'joined_date', 'is_active', 'notes']
    readonly_fields = []
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'church', 'group_type', 'parent_group', 
        'leader_display', 'member_count_display', 'management_type', 
        'is_active', 'created_at'
    ]
    list_filter = [
        'church', 'group_type', 'management_type', 'is_active', 
        'created_at', 'parent_group'
    ]
    search_fields = [
        'name', 'code', 'description', 'church__name', 
        'leader__name', 'meeting_place'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'member_count_display', 
        'is_full_display', 'hierarchy_name_display'
    ]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'name', 'code', 'description')
        }),
        ('그룹 분류', {
            'fields': ('group_type', 'parent_group', 'order')
        }),
        ('관리 설정', {
            'fields': ('management_type', 'age_min', 'age_max', 'max_members'),
            'classes': ('collapse',)
        }),
        ('담당자 정보', {
            'fields': ('leader',),
            'classes': ('collapse',)
        }),
        ('모임 정보', {
            'fields': ('meeting_day', 'meeting_time', 'meeting_place'),
            'classes': ('collapse',)
        }),
        ('상태 정보', {
            'fields': ('is_active', 'member_count_display', 'is_full_display'),
            'classes': ('collapse',)
        }),
        ('계층 구조', {
            'fields': ('hierarchy_name_display',),
            'classes': ('collapse',)
        }),
        ('시스템 필드', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [GroupMemberInline]
    
    def leader_display(self, obj):
        """그룹장 표시"""
        if obj.leader:
            return format_html(
                '<a href="/admin/members/member/{}/change/">{}</a>',
                obj.leader.id, obj.leader.name
            )
        return '-'
    leader_display.short_description = '그룹장'
    
    def member_count_display(self, obj):
        """그룹 인원 표시"""
        count = obj.member_count
        if obj.max_members:
            percentage = (count / obj.max_members) * 100
            color = 'green' if percentage < 80 else 'orange' if percentage < 95 else 'red'
            return format_html(
                '<span style="color: {};">{} / {} ({}%)</span>',
                color, count, obj.max_members, round(percentage, 1)
            )
        return str(count)
    member_count_display.short_description = '인원'
    
    def is_full_display(self, obj):
        """정원 상태 표시"""
        if obj.is_full:
            return format_html('<span style="color: red;">정원 초과</span>')
        return format_html('<span style="color: green;">여유 있음</span>')
    is_full_display.short_description = '정원 상태'
    
    def hierarchy_name_display(self, obj):
        """계층 구조 표시"""
        return obj.get_hierarchy_name()
    hierarchy_name_display.short_description = '계층 구조'
    
    def get_queryset(self, request):
        """쿼리셋 최적화"""
        return super().get_queryset(request).select_related(
            'church', 'parent_group', 'leader', 'created_by'
        ).prefetch_related('group_members')
    
    def save_model(self, request, obj, form, change):
        """생성자 자동 설정"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = [
        'member_name', 'group_name', 'role', 'joined_date', 
        'is_active', 'church_name'
    ]
    list_filter = [
        'group__church', 'group', 'role', 'is_active', 
        'joined_date', 'group__group_type'
    ]
    search_fields = [
        'member__name', 'group__name', 'member__phone', 
        'group__church__name', 'notes'
    ]
    readonly_fields = ['church_name']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('group', 'member', 'role')
        }),
        ('가입 정보', {
            'fields': ('joined_date', 'is_active')
        }),
        ('추가 정보', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('참조 정보', {
            'fields': ('church_name',),
            'classes': ('collapse',)
        }),
    )
    
    def member_name(self, obj):
        """멤버 이름 표시"""
        return format_html(
            '<a href="/admin/members/member/{}/change/">{}</a>',
            obj.member.id, obj.member.name
        )
    member_name.short_description = '교인명'
    
    def group_name(self, obj):
        """그룹 이름 표시"""
        return format_html(
            '<a href="/admin/groups/group/{}/change/">{}</a>',
            obj.group.id, obj.group.name
        )
    group_name.short_description = '그룹명'
    
    def church_name(self, obj):
        """교회 이름 표시"""
        return obj.group.church.name
    church_name.short_description = '소속 교회'
    
    def get_queryset(self, request):
        """쿼리셋 최적화"""
        return super().get_queryset(request).select_related(
            'group', 'member', 'group__church'
        )