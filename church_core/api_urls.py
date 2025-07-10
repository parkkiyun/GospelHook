from django.urls import path, include
from rest_framework.routers import DefaultRouter
from church.views import ChurchViewSet

router = DefaultRouter()
router.register(r'churches', ChurchViewSet)

urlpatterns = [
    # 인증 관련 엔드포인트 (교회 독립적)
    path('', include('users.urls')),
    
    # 교회 관리 (슈퍼관리자용)
    path('', include(router.urls)),
    
    # 멀티테넌시 교회별 API 엔드포인트
    path('churches/<int:church_id>/members/', include('members.urls')),
    path('churches/<int:church_id>/groups/', include('groups.urls')),
    path('churches/<int:church_id>/attendance/', include('attendance.urls')),
    path('churches/<int:church_id>/prayers/', include('prayers.urls')),
    path('churches/<int:church_id>/bible/', include('bible.urls')),
    path('churches/<int:church_id>/carelog/', include('carelog.urls')),
    path('churches/<int:church_id>/bulletins/', include('bulletins.urls')),
    path('churches/<int:church_id>/worship/', include('worship.urls')),
    path('churches/<int:church_id>/education/', include('education.urls')),
    path('churches/<int:church_id>/announcements/', include('announcements.urls')),
    path('churches/<int:church_id>/volunteering/', include('volunteering.urls')),
    path('churches/<int:church_id>/offerings/', include('offerings.urls')),
    path('churches/<int:church_id>/surveys/', include('surveys.urls')),
    path('churches/<int:church_id>/reports/', include('reports.urls')),
]