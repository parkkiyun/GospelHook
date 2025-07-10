from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, ChurchUser


class ChurchUserInline(admin.TabularInline):
    """교회별 사용자 정보 인라인"""
    model = ChurchUser
    extra = 0
    fields = ['church', 'role', 'name', 'phone', 'is_active', 'joined_at']
    readonly_fields = ['joined_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('church')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """커스텀 사용자 어드민"""
    list_display = ['username', 'email', 'is_verified', 'is_superuser', 'is_active', 'last_login', 'created_at']
    list_filter = ['is_verified', 'is_superuser', 'is_staff', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    fieldsets = UserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('phone', 'is_verified')}),
        ('시스템 정보', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('추가 정보', {'fields': ('email', 'phone')}),
    )
    
    inlines = [ChurchUserInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('church_users')


@admin.register(ChurchUser)
class ChurchUserAdmin(admin.ModelAdmin):
    """교회별 사용자 관리"""
    list_display = ['user_email', 'church_name', 'role_display', 'name', 'is_active', 'joined_at']
    list_filter = ['church', 'role', 'is_active', 'joined_at']
    search_fields = ['user__email', 'user__username', 'church__name', 'name', 'phone']
    readonly_fields = ['joined_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'church', 'role')
        }),
        ('개인 정보', {
            'fields': ('name', 'phone')
        }),
        ('상태', {
            'fields': ('is_active', 'joined_at')
        }),
    )
    
    def user_email(self, obj):
        """사용자 이메일"""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id, obj.user.email
        )
    user_email.short_description = '사용자 이메일'
    
    def church_name(self, obj):
        """교회명"""
        return format_html(
            '<a href="/admin/church/church/{}/change/">{}</a>',
            obj.church.id, obj.church.name
        )
    church_name.short_description = '교회'
    
    def role_display(self, obj):
        """권한 표시"""
        role_colors = {
            'SUPER_ADMIN': 'red',
            'CHURCH_ADMIN': 'blue',
            'CHURCH_STAFF': 'green',
            'MEMBER': 'gray'
        }
        color = role_colors.get(obj.role, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_display.short_description = '권한'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'church')
    
