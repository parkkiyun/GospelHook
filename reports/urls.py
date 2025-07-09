from django.urls import path
from .views import AttendanceReportView, EducationReportView, CareLogReportView, NewMemberReportView

urlpatterns = [
    path('attendance/', AttendanceReportView.as_view(), name='attendance-report'),
    path('education/', EducationReportView.as_view(), name='education-report'),
    path('care-logs/', CareLogReportView.as_view(), name='carelog-report'),
    path('new-members/', NewMemberReportView.as_view(), name='new-member-report'),
]
