from rest_framework.routers import DefaultRouter
from .views import EducationProgramViewSet, EducationRegistrationViewSet

router = DefaultRouter()
router.register(r'programs', EducationProgramViewSet, basename='education-program')
router.register(r'registrations', EducationRegistrationViewSet, basename='education-registration')

urlpatterns = router.urls