from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AuthViewSet, ChurchUserViewSet

router = DefaultRouter()
router.register(r'church-users', ChurchUserViewSet, basename='church-users')

# JWT 토큰 기반 인증 엔드포인트
auth_viewset = AuthViewSet.as_view({
    'post': 'login'
})

urlpatterns = [
    # JWT 인증 엔드포인트 (/api/v1/auth/)
    path('auth/token/', auth_viewset, name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', AuthViewSet.as_view({'post': 'register'}), name='user_register'),
    path('auth/me/', AuthViewSet.as_view({'get': 'profile', 'patch': 'update_profile'}), name='user_profile'),
    path('auth/change-password/', AuthViewSet.as_view({'post': 'change_password'}), name='change_password'),
] + router.urls