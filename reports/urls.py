from rest_framework.routers import DefaultRouter
from .views import (
    ReportTemplateViewSet, ReportViewSet, DashboardViewSet,
    StatisticsSummaryViewSet, ReportScheduleViewSet, ExportLogViewSet
)

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='report-template')
router.register(r'', ReportViewSet, basename='report')
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'statistics', StatisticsSummaryViewSet, basename='statistics')
router.register(r'schedules', ReportScheduleViewSet, basename='report-schedule')
router.register(r'exports', ExportLogViewSet, basename='export-log')

urlpatterns = router.urls
