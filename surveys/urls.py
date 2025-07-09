from rest_framework.routers import DefaultRouter
from .views import SurveyViewSet, QuestionViewSet, AnswerViewSet

router = DefaultRouter()
router.register(r'', SurveyViewSet, basename='survey')

question_router = DefaultRouter()
question_router.register(r'questions', QuestionViewSet, basename='question')

answer_router = DefaultRouter()
answer_router.register(r'answers', AnswerViewSet, basename='answer')

urlpatterns = router.urls + question_router.urls + answer_router.urls
