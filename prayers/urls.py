from rest_framework.routers import DefaultRouter
from .views import PrayerViewSet, PrayerGroupViewSet

router = DefaultRouter()
router.register(r'', PrayerViewSet, basename='prayer')
router.register(r'groups', PrayerGroupViewSet, basename='prayer-group')

urlpatterns = router.urls
