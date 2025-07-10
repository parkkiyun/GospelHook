from django.contrib import admin
from django.utils.html import format_html
from .models import Member, FamilyRelationship, FamilyTree


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        'member_code', 'name', 'gender', 'age_display', 'position', 
        'church', 'status', 'phone', 'family_role', 'is_active'
    ]
    list_filter = [
        'church', 'status', 'gender', 'position', 'is_active', 
        'auto_group_enabled', 'lunar_birth'
    ]
    search_fields = ['name', 'member_code', 'phone', 'email', 'address']
    readonly_fields = ['age_display', 'age_group', 'days_until_birthday', 'created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('church', 'member_code', 'name', 'gender', 'birth_date', 'lunar_birth')
        }),
        ('연락처', {
            'fields': ('phone', 'email', 'address')
        }),
        ('가족 정보', {
            'fields': ('household', 'family_role')
        }),
        ('교회 정보', {
            'fields': ('position', 'baptism_date', 'confirmation_date', 'registration_date', 'profile_image')
        }),
        ('상태', {
            'fields': ('status', 'is_active', 'auto_group_enabled')
        }),
        ('추가 정보', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('age_display', 'age_group', 'days_until_birthday', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def age_display(self, obj):
        """나이 표시"""
        return f"{obj.age}세" if obj.age else "미상"
    age_display.short_description = '나이'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('church', 'household', 'created_by')


class FamilyRelationshipInline(admin.TabularInline):
    model = FamilyRelationship
    fk_name = 'from_member'
    extra = 0
    readonly_fields = ['is_confirmed', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('to_member', 'created_by')


@admin.register(FamilyRelationship)
class FamilyRelationshipAdmin(admin.ModelAdmin):
    list_display = [
        'from_member', 'relationship_display', 'to_member', 
        'relationship_detail', 'is_confirmed', 'church', 'created_at'
    ]
    list_filter = ['church', 'relationship', 'is_confirmed', 'created_at']
    search_fields = [
        'from_member__name', 'to_member__name', 
        'relationship_detail', 'notes'
    ]
    readonly_fields = ['church', 'is_confirmed', 'created_at', 'updated_at']
    
    fieldsets = (
        ('관계 정보', {
            'fields': ('from_member', 'to_member', 'relationship', 'relationship_detail')
        }),
        ('추가 정보', {
            'fields': ('notes', 'is_confirmed')
        }),
        ('시스템 정보', {
            'fields': ('church', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def relationship_display(self, obj):
        return obj.get_relationship_display()
    relationship_display.short_description = '관계'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'from_member', 'to_member', 'church', 'created_by'
        )


class FamilyTreeMemberInline(admin.TabularInline):
    model = FamilyTree.family_members.through
    extra = 0
    verbose_name = "가족 구성원"
    verbose_name_plural = "가족 구성원들"


@admin.register(FamilyTree)
class FamilyTreeAdmin(admin.ModelAdmin):
    list_display = [
        'family_name', 'root_member', 'member_count', 
        'church', 'is_active', 'created_at'
    ]
    list_filter = ['church', 'is_active', 'created_at']
    search_fields = ['family_name', 'root_member__name', 'description']
    readonly_fields = ['member_count', 'created_at', 'updated_at']
    inlines = [FamilyTreeMemberInline]
    
    fieldsets = (
        ('가족 정보', {
            'fields': ('church', 'family_name', 'root_member', 'description')
        }),
        ('상태', {
            'fields': ('is_active',)
        }),
        ('시스템 정보', {
            'fields': ('member_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        return obj.family_members.count()
    member_count.short_description = '구성원 수'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'church', 'root_member', 'created_by'
        ).prefetch_related('family_members')


# Member admin에 FamilyRelationship inline 추가
MemberAdmin.inlines = [FamilyRelationshipInline]