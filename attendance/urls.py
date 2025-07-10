from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, AttendanceTemplateViewSet

router = DefaultRouter()
router.register(r'', AttendanceViewSet, basename='attendance')
router.register(r'templates', AttendanceTemplateViewSet, basename='attendance-template')

urlpatterns = router.urls
