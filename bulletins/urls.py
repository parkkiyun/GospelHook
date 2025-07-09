from rest_framework.routers import DefaultRouter
from .views import BulletinViewSet

router = DefaultRouter()
router.register(r'', BulletinViewSet, basename='bulletin')

urlpatterns = router.urls
