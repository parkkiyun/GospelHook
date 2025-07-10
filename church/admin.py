from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Church


@admin.register(Church)
class ChurchAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'pastor_name', 'denomination', 'postal_code',
        'member_count_display', 'has_documents', 'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'denomination', 'denomination_region', 'timezone', 'created_at'
    ]
    search_fields = [
        'name', 'code', 'pastor_name', 'address', 'email', 'postal_code',
        'denomination', 'denomination_region', 'registration_number'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'member_count_display', 
        'local_time_display', 'is_full_display', 'has_documents'
    ]
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'code')
        }),
        ('연락처 정보', {
            'fields': ('address', 'postal_code', 'phone', 'email', 'website')
        }),
        ('담임목사 정보', {
            'fields': ('pastor_name', 'pastor_phone'),
            'classes': ('collapse',)
        }),
        ('교단 정보', {
            'fields': ('denomination', 'denomination_region', 'registration_number'),
            'classes': ('collapse',)
        }),
        ('교회 설정', {
            'fields': ('timezone', 'founding_date'),
            'classes': ('collapse',)
        }),
        ('이미지 업로드', {
            'fields': ('logo',)
        }),
        ('공식 문서 이미지', {
            'fields': (
                'church_seal', 'membership_certificate_header',
                'baptism_certificate_header', 'affiliation_certificate_header'
            ),
            'classes': ('collapse',)
        }),
        ('시스템 설정', {
            'fields': ('domain', 'is_active', 'max_members'),
            'classes': ('collapse',)
        }),
        ('커스텀 설정', {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        ('통계 정보', {
            'fields': ('member_count_display', 'is_full_display', 'local_time_display', 'has_documents'),
            'classes': ('collapse',)
        }),
        ('시스템 필드', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count_display(self, obj):
        """교인 수 표시"""
        try:
            count = obj.member_count
            if obj.max_members:
                percentage = (count / obj.max_members) * 100
                color = 'green' if percentage < 80 else 'orange' if percentage < 95 else 'red'
                return format_html(
                    '<span style="color: {};">{} / {} ({}%)</span>',
                    color, count, obj.max_members, round(percentage, 1)
                )
            return str(count)
        except:
            return '0'
    member_count_display.short_description = '교인 수'
    
    def is_full_display(self, obj):
        """정원 초과 여부 표시"""
        try:
            is_full = obj.is_full
            if is_full:
                return format_html('<span style="color: red;">정원 초과</span>')
            return format_html('<span style="color: green;">여유 있음</span>')
        except:
            return '-'
    is_full_display.short_description = '정원 상태'
    
    def local_time_display(self, obj):
        """교회 현지 시간 표시"""
        try:
            local_time = obj.get_local_time()
            return local_time.strftime('%Y-%m-%d %H:%M:%S %Z')
        except:
            return '-'
    local_time_display.short_description = '현지 시간'
    
    def has_documents(self, obj):
        """공식 문서 이미지 보유 여부"""
        docs = [
            obj.church_seal,
            obj.membership_certificate_header,
            obj.baptism_certificate_header,
            obj.affiliation_certificate_header
        ]
        has_count = sum(1 for doc in docs if doc)
        total_count = len(docs)
        
        if has_count == total_count:
            color = 'green'
            text = f'완료 ({has_count}/{total_count})'
        elif has_count > 0:
            color = 'orange'
            text = f'부분 ({has_count}/{total_count})'
        else:
            color = 'red'
            text = f'없음 (0/{total_count})'
            
        return format_html('<span style="color: {};">{}</span>', color, text)
    has_documents.short_description = '공식문서'
    
    def get_queryset(self, request):
        """쿼리셋 최적화"""
        return super().get_queryset(request).prefetch_related('members')
    
    def save_model(self, request, obj, form, change):
        """코드 자동 생성"""
        if not obj.code and obj.name:
            # 교회 이름을 기반으로 코드 생성
            import re
            code_base = re.sub(r'[^A-Za-z0-9가-힣]', '', obj.name)[:10].upper()
            if code_base:
                counter = 1
                original_code = code_base
                while Church.objects.filter(code=code_base).exists():
                    code_base = f"{original_code}{counter:02d}"
                    counter += 1
                obj.code = code_base
        super().save_model(request, obj, form, change)