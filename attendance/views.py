from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Attendance
from .serializers import AttendanceSerializer
from church_core.permissions import IsChurchMember, IsPastor
from rolepermissions.roles import get_user_roles

class AttendanceViewSet(viewsets.ModelViewSet):
    """
    출석(Attendance)에 대한 API ViewSet
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 출석 기록만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)

    def create(self, request, *args, **kwargs):
        # 출석 기록 생성은 슈퍼유저, PASTOR, ELDER, TEACHER만 가능
        user_roles = [role.name for role in get_user_roles(request.user)]
        if not (request.user.is_superuser or IsPastor().has_permission(request, self) or 'ELDER' in user_roles or 'TEACHER' in user_roles):
            return Response({"detail": "출석 기록 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # 출석 기록 수정은 슈퍼유저, PASTOR, ELDER, TEACHER만 가능
        user_roles = [role.name for role in get_user_roles(request.user)]
        if not (request.user.is_superuser or IsPastor().has_permission(request, self) or 'ELDER' in user_roles or 'TEACHER' in user_roles):
            return Response({"detail": "출석 기록 수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # 출석 기록 삭제는 슈퍼유저, PASTOR, ELDER, TEACHER만 가능
        user_roles = [role.name for role in get_user_roles(request.user)]
        if not (request.user.is_superuser or IsPastor().has_permission(request, self) or 'ELDER' in user_roles or 'TEACHER' in user_roles):
            return Response({"detail": "출석 기록 삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
