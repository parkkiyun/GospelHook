from django.contrib import admin
from django.utils.html import format_html
from .models import UserSecurityProfile, JWTBlacklist, ActivityLog


@admin.register(UserSecurityProfile)
class UserSecurityProfileAdmin(admin.ModelAdmin):
    """사용자 보안 프로필 관리"""
    list_display = ['user_email', 'failed_attempts', 'is_locked_display', 'last_failed_login', 'password_changed_at']
    list_filter = ['locked_until', 'password_changed_at', 'last_failed_login']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['user', 'failed_login_attempts', 'last_failed_login', 'password_changed_at']
    
    fieldsets = (
        ('사용자 정보', {
            'fields': ('user',)
        }),
        ('보안 상태', {
            'fields': ('failed_login_attempts', 'locked_until', 'last_failed_login')
        }),
        ('비밀번호 관리', {
            'fields': ('password_changed_at',)
        }),
        ('로그인 추적', {
            'fields': ('last_login_ip',)
        }),
    )
    
    def user_email(self, obj):
        """사용자 이메일"""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id, obj.user.email
        )
    user_email.short_description = '사용자 이메일'
    
    def failed_attempts(self, obj):
        """실패 횟수 표시"""
        if obj.failed_login_attempts >= 5:
            color = 'red'
        elif obj.failed_login_attempts >= 3:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.failed_login_attempts
        )
    failed_attempts.short_description = '로그인 실패 횟수'
    
    def is_locked_display(self, obj):
        """잠금 상태 표시"""
        if obj.is_locked:
            return format_html(
                '<span style="color: red; font-weight: bold;">🔒 잠김</span>'
            )
        return format_html(
            '<span style="color: green;">🔓 활성</span>'
        )
    is_locked_display.short_description = '계정 상태'
    
    actions = ['unlock_accounts']
    
    def unlock_accounts(self, request, queryset):
        """선택된 계정들 잠금 해제"""
        count = 0
        for profile in queryset:
            if profile.is_locked:
                profile.unlock_account()
                count += 1
        
        self.message_user(request, f'{count}개 계정의 잠금을 해제했습니다.')
    unlock_accounts.short_description = '선택된 계정 잠금 해제'


@admin.register(JWTBlacklist)
class JWTBlacklistAdmin(admin.ModelAdmin):
    """JWT 블랙리스트 관리"""
    list_display = ['user_email', 'token_preview', 'reason_display', 'blacklisted_at', 'expires_at']
    list_filter = ['reason', 'blacklisted_at', 'expires_at']
    search_fields = ['user__email', 'user__username', 'token_jti']
    readonly_fields = ['token_jti', 'user', 'blacklisted_at']
    
    fieldsets = (
        ('토큰 정보', {
            'fields': ('token_jti', 'user', 'expires_at')
        }),
        ('블랙리스트 정보', {
            'fields': ('reason', 'blacklisted_at')
        }),
    )
    
    def user_email(self, obj):
        """사용자 이메일"""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id, obj.user.email
        )
    user_email.short_description = '사용자'
    
    def token_preview(self, obj):
        """토큰 미리보기"""
        return f"{obj.token_jti[:12]}..."
    token_preview.short_description = 'JWT ID'
    
    def reason_display(self, obj):
        """블랙리스트 사유 표시"""
        colors = {
            'logout': 'green',
            'security': 'red',
            'expired': 'orange',
            'revoked': 'purple'
        }
        color = colors.get(obj.reason, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_reason_display()
        )
    reason_display.short_description = '블랙리스트 사유'
    
    actions = ['cleanup_expired']
    
    def cleanup_expired(self, request, queryset):
        """만료된 토큰 정리"""
        deleted_count, _ = JWTBlacklist.cleanup_expired()
        self.message_user(request, f'{deleted_count}개의 만료된 토큰을 정리했습니다.')
    cleanup_expired.short_description = '만료된 토큰 정리'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """활동 로그 관리"""
    list_display = ['user_email', 'action_display', 'resource', 'church_name', 'ip_address', 'created_at']
    list_filter = ['action', 'resource', 'created_at', 'church']
    search_fields = ['user__email', 'user__username', 'action', 'resource', 'ip_address']
    readonly_fields = ['user', 'church', 'action', 'resource', 'resource_id', 'ip_address', 'user_agent', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('사용자 정보', {
            'fields': ('user', 'church')
        }),
        ('활동 정보', {
            'fields': ('action', 'resource', 'resource_id')
        }),
        ('기술 정보', {
            'fields': ('ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """사용자 이메일"""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id, obj.user.email
        )
    user_email.short_description = '사용자'
    
    def church_name(self, obj):
        """교회명"""
        if obj.church:
            return format_html(
                '<a href="/admin/church/church/{}/change/">{}</a>',
                obj.church.id, obj.church.name
            )
        return '-'
    church_name.short_description = '교회'
    
    def action_display(self, obj):
        """액션 표시"""
        if 'POST' in obj.action:
            color = 'blue'
        elif 'PUT' in obj.action or 'PATCH' in obj.action:
            color = 'orange'
        elif 'DELETE' in obj.action:
            color = 'red'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.action
        )
    action_display.short_description = '액션'
    
    def has_add_permission(self, request):
        """로그 추가 금지"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """로그 수정 금지"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """로그 삭제 허용 (정리 목적)"""
        return request.user.is_superuser
