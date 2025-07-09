from rest_framework.routers import DefaultRouter
from .views import WorshipRecordViewSet

router = DefaultRouter()
router.register(r'', WorshipRecordViewSet, basename='worship-record')

urlpatterns = router.urls
