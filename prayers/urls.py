from rest_framework.routers import DefaultRouter
from .views import PrayerViewSet

router = DefaultRouter()
router.register(r'', PrayerViewSet, basename='prayer')

urlpatterns = router.urls
