from django.contrib import admin
from django.utils.html import format_html
from .models import Prayer, PrayerComment, PrayerGroup, PrayerGroupMember


class PrayerCommentInline(admin.TabularInline):
    model = PrayerComment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Prayer)
class PrayerAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'member', 'prayer_type', 'priority', 'status',
        'prayer_date', 'target_date', 'prayer_count', 'is_public', 'church'
    ]
    list_filter = [
        'church', 'prayer_type', 'priority', 'status', 'is_public',
        'is_shared_with_leaders', 'prayer_date', 'target_date'
    ]
    search_fields = ['title', 'content', 'member__name', 'tags', 'answer_note']
    readonly_fields = ['prayer_count', 'answered_date', 'created_at', 'updated_at']
    inlines = [PrayerCommentInline]
    
    fieldsets = (
        ('기도제목 정보', {
            'fields': ('church', 'member', 'title', 'content', 'prayer_type', 'priority')
        }),
        ('상태', {
            'fields': ('status', 'is_public', 'is_shared_with_leaders')
        }),
        ('일정', {
            'fields': ('prayer_date', 'target_date', 'answered_date')
        }),
        ('분류', {
            'fields': ('group', 'tags')
        }),
        ('응답 및 메모', {
            'fields': ('answer_note', 'private_note'),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('prayer_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('church', 'member', 'group', 'created_by')


@admin.register(PrayerComment)
class PrayerCommentAdmin(admin.ModelAdmin):
    list_display = ['prayer', 'member', 'content_preview', 'is_encouragement', 'is_private', 'created_at']
    list_filter = ['is_encouragement', 'is_private', 'created_at']
    search_fields = ['prayer__title', 'member__name', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = '내용 미리보기'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('prayer', 'member')


class PrayerGroupMemberInline(admin.TabularInline):
    model = PrayerGroupMember
    extra = 0
    readonly_fields = ['joined_date']


@admin.register(PrayerGroup)
class PrayerGroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'church', 'member_count', 'meeting_day', 
        'meeting_time', 'is_public', 'is_active'
    ]
    list_filter = ['church', 'is_public', 'is_active', 'meeting_day']
    search_fields = ['name', 'description']
    readonly_fields = ['member_count', 'created_at', 'updated_at']
    inlines = [PrayerGroupMemberInline]
    
    def member_count(self, obj):
        return obj.group_members.filter(is_active=True).count()
    member_count.short_description = '활성 멤버 수'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('church', 'created_by')


@admin.register(PrayerGroupMember)
class PrayerGroupMemberAdmin(admin.ModelAdmin):
    list_display = ['prayer_group', 'member', 'role', 'joined_date', 'is_active']
    list_filter = ['role', 'is_active', 'joined_date']
    search_fields = ['prayer_group__name', 'member__name']
    readonly_fields = ['joined_date']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('prayer_group', 'member')