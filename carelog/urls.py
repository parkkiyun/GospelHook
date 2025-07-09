from rest_framework.routers import DefaultRouter
from .views import CareLogViewSet

router = DefaultRouter()
router.register(r'', CareLogViewSet, basename='carelog')

urlpatterns = router.urls
