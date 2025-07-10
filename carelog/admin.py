from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from datetime import date, timedelta
from .models import CareLog


@admin.register(CareLog)
class CareLogAdmin(admin.ModelAdmin):
    list_display = [
        'member_name', 'church_name', 'type_display', 'date', 
        'content_preview', 'created_by', 'created_at'
    ]
    list_filter = [
        'church', 'type', 'date', 'created_by', 'created_at'
    ]
    search_fields = [
        'member__name', 'member__phone', 'church__name', 
        'content', 'created_by__username'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'church_name', 'member_info_display'
    ]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'member', 'type', 'date')
        }),
        ('내용', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('시스템 정보', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('참조 정보', {
            'fields': ('church_name', 'member_info_display'),
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
    
    def type_display(self, obj):
        """기록 유형 표시"""
        type_colors = {
            'PRAYER': 'purple',
            'NEWS': 'blue',
            'HOSPITAL_VISIT': 'green',
            'ETC': 'gray'
        }
        color = type_colors.get(obj.type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_type_display()
        )
    type_display.short_description = '기록 유형'
    
    def content_preview(self, obj):
        """내용 미리보기"""
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    content_preview.short_description = '내용 미리보기'
    
    def member_info_display(self, obj):
        """교인 정보 표시"""
        member = obj.member
        info_parts = [f"이름: {member.name}"]
        
        if hasattr(member, 'phone') and member.phone:
            info_parts.append(f"연락처: {member.phone}")
        
        if hasattr(member, 'birth_date') and member.birth_date:
            info_parts.append(f"생년월일: {member.birth_date}")
        
        if hasattr(member, 'address') and member.address:
            info_parts.append(f"주소: {member.address}")
        
        return format_html('<br>'.join(info_parts))
    member_info_display.short_description = '교인 정보'
    
    def get_queryset(self, request):
        """쿼리셋 최적화"""
        return super().get_queryset(request).select_related(
            'church', 'member', 'created_by'
        )
    
    def save_model(self, request, obj, form, change):
        """생성자 자동 설정"""
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_prayer', 'mark_as_news', 'mark_as_hospital_visit']
    
    def mark_as_prayer(self, request, queryset):
        """기도 유형으로 변경"""
        updated = queryset.update(type='PRAYER')
        self.message_user(request, f'{updated}개의 기록이 기도 유형으로 변경되었습니다.')
    mark_as_prayer.short_description = '선택된 항목을 기도 유형으로 변경'
    
    def mark_as_news(self, request, queryset):
        """생활소식 유형으로 변경"""
        updated = queryset.update(type='NEWS')
        self.message_user(request, f'{updated}개의 기록이 생활소식 유형으로 변경되었습니다.')
    mark_as_news.short_description = '선택된 항목을 생활소식 유형으로 변경'
    
    def mark_as_hospital_visit(self, request, queryset):
        """병문안 유형으로 변경"""
        updated = queryset.update(type='HOSPITAL_VISIT')
        self.message_user(request, f'{updated}개의 기록이 병문안 유형으로 변경되었습니다.')
    mark_as_hospital_visit.short_description = '선택된 항목을 병문안 유형으로 변경'
    
    def get_form(self, request, obj=None, **kwargs):
        """폼 커스터마이징"""
        form = super().get_form(request, obj, **kwargs)
        
        # 기본 날짜를 오늘로 설정
        if not obj:
            form.base_fields['date'].initial = date.today()
        
        return form
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """필드별 커스터마이징"""
        if db_field.name == 'content':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget(
                attrs={'rows': 6, 'cols': 80}
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)