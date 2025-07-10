from rest_framework.routers import DefaultRouter
from .views import SurveyViewSet, QuestionViewSet, AnswerViewSet

router = DefaultRouter()
router.register(r'surveys', SurveyViewSet, basename='survey')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'answers', AnswerViewSet, basename='answer')

urlpatterns = router.urls
