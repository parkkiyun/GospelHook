from rest_framework.routers import DefaultRouter
from .views import VolunteerApplicationViewSet, VolunteerRoleViewSet, VolunteerAssignmentViewSet

router = DefaultRouter()
router.register(r'applications', VolunteerApplicationViewSet, basename='volunteer-application')
router.register(r'roles', VolunteerRoleViewSet, basename='volunteer-role')
router.register(r'assignments', VolunteerAssignmentViewSet, basename='volunteer-assignment')

urlpatterns = router.urls
