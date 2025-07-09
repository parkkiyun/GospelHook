from rest_framework.routers import DefaultRouter
from .views import OfferingViewSet

router = DefaultRouter()
router.register(r'', OfferingViewSet, basename='offering')

urlpatterns = router.urls
