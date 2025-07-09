from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from church_core.permissions import IsChurchMember, IsPastor

class AttendanceReportView(APIView):
    permission_classes = [IsAuthenticated, IsChurchMember, IsPastor]

    def get(self, request, church_id, format=None):
        # TODO: 실제 예배 출석 통계 로직 구현 (일자별/부서별)
        return Response({
            "report_name": "예배 출석 통계",
            "church_id": church_id,
            "data": [
                {"date": "2024-07-01", "total_attendees": 100, "department_A": 30, "department_B": 70},
                {"date": "2024-07-08", "total_attendees": 120, "department_A": 40, "department_B": 80},
            ]
        }, status=status.HTTP_200_OK)

class EducationReportView(APIView):
    permission_classes = [IsAuthenticated, IsChurchMember, IsPastor]

    def get(self, request, church_id, format=None):
        # TODO: 실제 교육 신청/수료율 통계 로직 구현
        return Response({
            "report_name": "교육 신청/수료율",
            "church_id": church_id,
            "data": [
                {"program": "새신자 교육", "applied": 50, "completed": 45, "completion_rate": "90%"},
                {"program": "제자 훈련", "applied": 20, "completed": 15, "completion_rate": "75%"},
            ]
        }, status=status.HTTP_200_OK)

class CareLogReportView(APIView):
    permission_classes = [IsAuthenticated, IsChurchMember, IsPastor]

    def get(self, request, church_id, format=None):
        # TODO: 실제 CareLog 기록 추이 통계 로직 구현
        return Response({
            "report_name": "생활소식/심방 기록 추이",
            "church_id": church_id,
            "data": [
                {"month": "2024-05", "prayer_logs": 10, "news_logs": 5, "hospital_visits": 2},
                {"month": "2024-06", "prayer_logs": 12, "news_logs": 7, "hospital_visits": 3},
            ]
        }, status=status.HTTP_200_OK)

class NewMemberReportView(APIView):
    permission_classes = [IsAuthenticated, IsChurchMember, IsPastor]

    def get(self, request, church_id, format=None):
        # TODO: 실제 새가족 정착 현황 통계 로직 구현
        return Response({
            "report_name": "새가족 정착 현황",
            "church_id": church_id,
            "data": [
                {"year": 2023, "new_members": 30, "settled_members": 25, "settlement_rate": "83.3%"},
                {"year": 2024, "new_members": 25, "settled_members": 20, "settlement_rate": "80%"},
            ]
        }, status=status.HTTP_200_OK)