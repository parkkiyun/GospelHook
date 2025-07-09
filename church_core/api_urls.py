from django.urls import path, include
from church.views import ChurchViewSet

app_name = 'api'

urlpatterns = [
    path('auth/', include('users.urls')),
    path('churches/', ChurchViewSet.as_view({'post': 'create'}), name='church-list-create'), # For creating churches
    path('churches/<int:church_id>/', include([
        path('', include('church.urls')), # For operations on the church itself (retrieve, update, delete)
        path('members/', include('members.urls')), # For members within that church
        path('users/', include('users.urls')), # For users within that church
        path('groups/', include('groups.urls')), # For groups within that church
        path('attendance/', include('attendance.urls')), # For attendance within that church
        path('prayers/', include('prayers.urls')), # For prayers within that church
        path('care-logs/', include('carelog.urls')), # For care logs within that church
        path('bulletins/', include('bulletins.urls')), # For bulletins within that church
        path('education/', include('education.urls')), # For education within that church
        path('worship-records/', include('worship.urls')), # For worship records within that church
        path('announcements/', include('announcements.urls')), # For announcements within that church
        path('volunteer/', include('volunteering.urls')), # For volunteering within that church
        path('reports/', include('reports.urls')), # For reports within that church
        path('offerings/', include('offerings.urls')), # For offerings within that church
        path('surveys/', include('surveys.urls')), # For surveys within that church
        path('bible/', include('bible.urls')), # For bible integration within that church
        # ... and so on for other resources
        # ... and so on for other resources
    ])),
]