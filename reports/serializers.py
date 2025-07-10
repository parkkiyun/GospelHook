from rest_framework import serializers
from django.utils import timezone
from .models import (
    ReportTemplate, Report, Dashboard, StatisticsSummary,
    ReportSchedule, ExportLog, MinistryReport, 
    MinistryReportTemplate, MinistryReportComment
)
from users.serializers import ChurchUserSerializer
from groups.serializers import GroupSerializer
from volunteering.serializers import VolunteerRoleSerializer


class ReportTemplateSerializer(serializers.ModelSerializer):
    """리포트 템플릿 시리얼라이저"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_type', 'config',
            'is_auto_generate', 'generate_frequency', 'last_generated',
            'is_active', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_generated', 'created_at', 'updated_at']


class ReportTemplateListSerializer(serializers.ModelSerializer):
    """리포트 템플릿 목록용 시리얼라이저"""
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'report_type',
            'is_auto_generate', 'generate_frequency', 'is_active'
        ]


class ReportSerializer(serializers.ModelSerializer):
    """리포트 시리얼라이저"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'template', 'template_name', 'title', 'start_date', 'end_date',
            'data', 'summary', 'status', 'error_message', 'pdf_file', 'excel_file',
            'generated_by_name', 'generated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'status', 'error_message', 'generated_at', 'completed_at']


class ReportListSerializer(serializers.ModelSerializer):
    """리포트 목록용 시리얼라이저"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'template_name', 'title', 'start_date', 'end_date',
            'status', 'generated_at', 'completed_at'
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    """리포트 생성용 시리얼라이저"""
    template_id = serializers.IntegerField()
    
    class Meta:
        model = Report
        fields = ['template_id', 'title', 'start_date', 'end_date']
    
    def validate(self, attrs):
        """유효성 검사"""
        template_id = attrs.get('template_id')
        try:
            template = ReportTemplate.objects.get(id=template_id)
            attrs['template'] = template
        except ReportTemplate.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 템플릿입니다.")
        
        return attrs


class DashboardSerializer(serializers.ModelSerializer):
    """대시보드 시리얼라이저"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'layout', 'widgets',
            'is_public', 'allowed_roles', 'auto_refresh', 'refresh_interval',
            'is_active', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardListSerializer(serializers.ModelSerializer):
    """대시보드 목록용 시리얼라이저"""
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'is_public', 'auto_refresh',
            'refresh_interval', 'is_active'
        ]


class StatisticsSummarySerializer(serializers.ModelSerializer):
    """통계 요약 시리얼라이저"""
    
    class Meta:
        model = StatisticsSummary
        fields = [
            'id', 'date', 'total_members', 'active_members',
            'new_members_today', 'new_members_this_month',
            'sunday_attendance', 'wednesday_attendance',
            'total_attendance_this_week', 'attendance_rate',
            'total_groups', 'active_groups', 'total_prayers',
            'active_prayers', 'answered_prayers_today',
            'total_offerings_today', 'total_offerings_this_month',
            'calculated_at'
        ]
        read_only_fields = ['id', 'calculated_at']


class ReportScheduleSerializer(serializers.ModelSerializer):
    """리포트 스케줄 시리얼라이저"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    notification_emails_list = serializers.ListField(source='get_notification_emails_list', read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'template', 'template_name', 'cron_expression',
            'next_run', 'last_run', 'is_running', 'last_success',
            'error_count', 'notify_on_success', 'notify_on_failure',
            'notification_emails', 'notification_emails_list',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run', 'is_running', 'last_success', 'error_count', 'created_at', 'updated_at']


class ExportLogSerializer(serializers.ModelSerializer):
    """내보내기 로그 시리얼라이저"""
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    
    class Meta:
        model = ExportLog
        fields = [
            'id', 'export_type', 'status', 'filters', 'file_path',
            'file_size', 'record_count', 'error_message',
            'requested_by_name', 'requested_at', 'completed_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'status', 'file_path', 'file_size', 'record_count',
            'error_message', 'requested_at', 'completed_at', 'expires_at'
        ]


class ExportLogCreateSerializer(serializers.ModelSerializer):
    """내보내기 로그 생성용 시리얼라이저"""
    
    class Meta:
        model = ExportLog
        fields = ['export_type', 'filters']


class StatisticsOverviewSerializer(serializers.Serializer):
    """통계 개요용 시리얼라이저"""
    members = serializers.DictField()
    attendance = serializers.DictField()
    prayers = serializers.DictField()
    groups = serializers.DictField()
    offerings = serializers.DictField()
    recent_activities = serializers.ListField()


class MinistryReportCommentSerializer(serializers.ModelSerializer):
    """사역 보고서 댓글 시리얼라이저"""
    author = ChurchUserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = MinistryReportComment
        fields = [
            'id', 'content', 'comment_type', 'author', 'parent',
            'replies', 'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_replies(self, obj):
        """대댓글 목록 반환"""
        if obj.replies.filter(is_deleted=False).exists():
            return MinistryReportCommentSerializer(
                obj.replies.filter(is_deleted=False), 
                many=True, 
                context=self.context
            ).data
        return []

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user.church_user
        return super().create(validated_data)


class MinistryReportListSerializer(serializers.ModelSerializer):
    """사역 보고서 목록용 시리얼라이저"""
    reporter = ChurchUserSerializer(read_only=True)
    department = GroupSerializer(read_only=True)
    volunteer_role = VolunteerRoleSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    attachment_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    days_since_report = serializers.ReadOnlyField()

    class Meta:
        model = MinistryReport
        fields = [
            'id', 'title', 'category', 'category_display', 'priority', 
            'priority_display', 'status', 'status_display', 'report_date',
            'reporter', 'department', 'volunteer_role', 'summary',
            'attendance_count', 'budget_used', 'attachment_count',
            'comment_count', 'days_since_report', 'is_public',
            'created_at', 'updated_at', 'submitted_at'
        ]

    def get_attachment_count(self, obj):
        return obj.get_attachment_count()

    def get_comment_count(self, obj):
        return obj.comments.filter(is_deleted=False).count()


class MinistryReportDetailSerializer(serializers.ModelSerializer):
    """사역 보고서 상세용 시리얼라이저"""
    reporter = ChurchUserSerializer(read_only=True)
    department = GroupSerializer(read_only=True)
    volunteer_role = VolunteerRoleSerializer(read_only=True)
    reviewer = ChurchUserSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    comments = MinistryReportCommentSerializer(many=True, read_only=True)
    attachment_count = serializers.SerializerMethodField()
    days_since_report = serializers.ReadOnlyField()
    is_editable = serializers.ReadOnlyField()

    class Meta:
        model = MinistryReport
        fields = [
            'id', 'title', 'category', 'category_display', 'priority', 
            'priority_display', 'status', 'status_display', 'report_date',
            'start_date', 'end_date', 'reporter', 'department', 'volunteer_role',
            'summary', 'content', 'achievements', 'challenges', 'next_plans',
            'prayer_requests', 'attendance_count', 'new_members_count',
            'budget_used', 'budget_remaining', 'custom_data', 'attachments',
            'reviewer', 'reviewed_at', 'review_comments', 'tags',
            'is_public', 'attachment_count', 'days_since_report', 'is_editable',
            'comments', 'created_at', 'updated_at', 'submitted_at'
        ]

    def get_attachment_count(self, obj):
        return obj.get_attachment_count()


class MinistryReportCreateSerializer(serializers.ModelSerializer):
    """사역 보고서 생성용 시리얼라이저"""
    
    class Meta:
        model = MinistryReport
        fields = [
            'title', 'category', 'priority', 'report_date', 'start_date', 
            'end_date', 'department', 'volunteer_role', 'summary', 'content',
            'achievements', 'challenges', 'next_plans', 'prayer_requests',
            'attendance_count', 'new_members_count', 'budget_used', 
            'budget_remaining', 'custom_data', 'attachments', 'tags', 'is_public'
        ]

    def create(self, validated_data):
        validated_data['church'] = self.context['church']
        validated_data['reporter'] = self.context['request'].user.church_user
        return super().create(validated_data)

    def validate_report_date(self, value):
        """보고 날짜 검증"""
        if value > timezone.now().date():
            raise serializers.ValidationError("보고 날짜는 미래일 수 없습니다.")
        return value

    def validate(self, data):
        """전체 데이터 검증"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'end_date': '종료일은 시작일보다 늦어야 합니다.'
                })
        
        if data.get('budget_used') and data.get('budget_remaining'):
            if data['budget_used'] < 0 or data['budget_remaining'] < 0:
                raise serializers.ValidationError({
                    'budget_used': '예산 금액은 음수일 수 없습니다.'
                })
        
        return data


class MinistryReportUpdateSerializer(serializers.ModelSerializer):
    """사역 보고서 수정용 시리얼라이저"""
    
    class Meta:
        model = MinistryReport
        fields = [
            'title', 'category', 'priority', 'report_date', 'start_date', 
            'end_date', 'department', 'volunteer_role', 'summary', 'content',
            'achievements', 'challenges', 'next_plans', 'prayer_requests',
            'attendance_count', 'new_members_count', 'budget_used', 
            'budget_remaining', 'custom_data', 'attachments', 'tags', 'is_public'
        ]

    def validate(self, data):
        """수정 가능 여부 검증"""
        if not self.instance.is_editable:
            raise serializers.ValidationError(
                "현재 상태에서는 보고서를 수정할 수 없습니다."
            )
        return super().validate(data)


class MinistryReportTemplateSerializer(serializers.ModelSerializer):
    """사역 보고서 템플릿 시리얼라이저"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    target_roles = VolunteerRoleSerializer(many=True, read_only=True)
    target_groups = GroupSerializer(many=True, read_only=True)
    default_reviewers = ChurchUserSerializer(many=True, read_only=True)
    created_by = ChurchUserSerializer(read_only=True)

    class Meta:
        model = MinistryReportTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_display',
            'fields_config', 'required_fields', 'auto_create', 
            'auto_create_schedule', 'target_roles', 'target_groups',
            'requires_approval', 'default_reviewers', 'is_active',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['church'] = self.context['church']
        validated_data['created_by'] = self.context['request'].user.church_user
        return super().create(validated_data)


class MinistryReportStatusUpdateSerializer(serializers.Serializer):
    """사역 보고서 상태 변경용 시리얼라이저"""
    status = serializers.ChoiceField(choices=MinistryReport.Status.choices)
    comments = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        """상태 변경 검증"""
        current_status = self.instance.status
        
        # 상태 변경 규칙
        allowed_transitions = {
            MinistryReport.Status.DRAFT: [MinistryReport.Status.SUBMITTED],
            MinistryReport.Status.SUBMITTED: [
                MinistryReport.Status.REVIEWED, 
                MinistryReport.Status.APPROVED,
                MinistryReport.Status.REJECTED
            ],
            MinistryReport.Status.REVIEWED: [
                MinistryReport.Status.APPROVED,
                MinistryReport.Status.REJECTED
            ],
            MinistryReport.Status.REJECTED: [MinistryReport.Status.SUBMITTED],
            MinistryReport.Status.APPROVED: [MinistryReport.Status.ARCHIVED],
        }
        
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"'{current_status}'에서 '{value}' 상태로 변경할 수 없습니다."
            )
        
        return value

    def update(self, instance, validated_data):
        status = validated_data['status']
        comments = validated_data.get('comments', '')
        user = self.context['request'].user.church_user
        
        if status == MinistryReport.Status.SUBMITTED:
            instance.submit()
        elif status == MinistryReport.Status.APPROVED:
            instance.approve(user, comments)
        elif status == MinistryReport.Status.REJECTED:
            instance.reject(user, comments)
        elif status == MinistryReport.Status.ARCHIVED:
            instance.archive()
        else:
            instance.status = status
            instance.save()
        
        return instance