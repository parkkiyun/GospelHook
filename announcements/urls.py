from rest_framework.routers import DefaultRouter
from .views import AnnouncementViewSet, PushLogViewSet

router = DefaultRouter()
router.register(r'', AnnouncementViewSet, basename='announcement')

push_log_router = DefaultRouter()
push_log_router.register(r'push-logs', PushLogViewSet, basename='push-log')

urlpatterns = router.urls + push_log_router.urls