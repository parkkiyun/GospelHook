from django.contrib import admin
from django.utils.html import format_html
from .models import (
    BibleVersion, BibleBook, BibleVerse, SermonScripture,
    DailyVerse, BibleStudy, BibleBookmark
)


@admin.register(BibleVersion)
class BibleVersionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'language', 'is_active']
    list_filter = ['language', 'is_active']
    search_fields = ['name', 'code', 'description']


@admin.register(BibleBook)
class BibleBookAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'testament', 'order', 'chapter_count']
    list_filter = ['testament']
    search_fields = ['name', 'code']
    ordering = ['order']


@admin.register(BibleVerse)
class BibleVerseAdmin(admin.ModelAdmin):
    list_display = ['reference', 'version', 'text_preview']
    list_filter = ['version', 'book__testament', 'book']
    search_fields = ['book__name', 'text']
    readonly_fields = ['reference']
    
    def text_preview(self, obj):
        return obj.text[:100] + "..." if len(obj.text) > 100 else obj.text
    text_preview.short_description = '본문 미리보기'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('version', 'book')


@admin.register(SermonScripture)
class SermonScriptureAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'preacher', 'date', 'main_scripture', 
        'service_type', 'church', 'has_audio', 'has_video'
    ]
    list_filter = ['church', 'service_type', 'date', 'preacher']
    search_fields = ['title', 'preacher', 'main_scripture', 'summary']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'title', 'preacher', 'date', 'service_type')
        }),
        ('본문', {
            'fields': ('main_scripture', 'sub_scriptures')
        }),
        ('설교 내용', {
            'fields': ('summary', 'outline', 'notes')
        }),
        ('파일', {
            'fields': ('audio_file', 'video_file', 'document_file')
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_audio(self, obj):
        return bool(obj.audio_file)
    has_audio.boolean = True
    has_audio.short_description = '음성파일'
    
    def has_video(self, obj):
        return bool(obj.video_file)
    has_video.boolean = True
    has_video.short_description = '영상파일'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('church', 'created_by')


@admin.register(DailyVerse)
class DailyVerseAdmin(admin.ModelAdmin):
    list_display = ['date', 'church', 'verse_reference', 'title', 'has_meditation']
    list_filter = ['church', 'date']
    search_fields = ['title', 'meditation', 'prayer', 'verse__text']
    readonly_fields = ['created_at', 'updated_at']
    
    def verse_reference(self, obj):
        return obj.verse.reference
    verse_reference.short_description = '성경 구절'
    
    def has_meditation(self, obj):
        return bool(obj.meditation)
    has_meditation.boolean = True
    has_meditation.short_description = '묵상'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('church', 'verse', 'created_by')


@admin.register(BibleStudy)
class BibleStudyAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'church', 'reference_range_display', 'leader', 
        'start_date', 'end_date', 'is_active'
    ]
    list_filter = ['church', 'is_active', 'start_date', 'leader']
    search_fields = ['title', 'description', 'leader__name']
    readonly_fields = ['reference_range', 'created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'title', 'description', 'leader', 'group')
        }),
        ('성경 범위', {
            'fields': (
                ('start_book', 'start_chapter', 'start_verse'),
                ('end_book', 'end_chapter', 'end_verse'),
                'reference_range'
            )
        }),
        ('일정', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def reference_range_display(self, obj):
        return obj.reference_range
    reference_range_display.short_description = '성경 범위'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'church', 'leader', 'group', 'start_book', 'end_book', 'created_by'
        )


@admin.register(BibleBookmark)
class BibleBookmarkAdmin(admin.ModelAdmin):
    list_display = [
        'member', 'verse_reference', 'title', 'color_display', 
        'church', 'created_at'
    ]
    list_filter = ['church', 'color', 'created_at']
    search_fields = ['member__name', 'title', 'note', 'verse__text']
    readonly_fields = ['created_at', 'updated_at']
    
    def verse_reference(self, obj):
        return obj.verse.reference
    verse_reference.short_description = '성경 구절'
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 6px; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = '색상'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('church', 'member', 'verse')
