from rest_framework.routers import DefaultRouter
from .views import VolunteerApplicationViewSet

router = DefaultRouter()
router.register(r'applications', VolunteerApplicationViewSet, basename='volunteer-application')

urlpatterns = router.urls
