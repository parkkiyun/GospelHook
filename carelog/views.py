from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CareLog
from .serializers import CareLogSerializer
from church_core.permissions import IsChurchMember, IsPastor
from rolepermissions.roles import get_user_roles

class CareLogViewSet(viewsets.ModelViewSet):
    """
    생활소식/심방기록(CareLog)에 대한 API ViewSet
    """
    queryset = CareLog.objects.all()
    serializer_class = CareLogSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 생활소식/심방기록만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)

    def perform_create(self, serializer):
        # CareLog 생성 시 작성자를 자동으로 현재 사용자로 설정
        serializer.save(created_by=self.request.user, church=self.request.user.church)

    def create(self, request, *args, **kwargs):
        # CareLog 생성은 슈퍼유저, PASTOR, ELDER, TEACHER만 가능
        user_roles = [role.name for role in get_user_roles(request.user)]
        if not (request.user.is_superuser or IsPastor().has_permission(request, self) or 'ELDER' in user_roles or 'TEACHER' in user_roles):
            return Response({"detail": "생활소식/심방기록 생성 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # CareLog 수정은 슈퍼유저, PASTOR, ELDER, TEACHER만 가능
        user_roles = [role.name for role in get_user_roles(request.user)]
        if not (request.user.is_superuser or IsPastor().has_permission(request, self) or 'ELDER' in user_roles or 'TEACHER' in user_roles):
            return Response({"detail": "생활소식/심방기록 수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # CareLog 삭제는 슈퍼유저, PASTOR, ELDER, TEACHER만 가능
        user_roles = [role.name for role in get_user_roles(request.user)]
        if not (request.user.is_superuser or IsPastor().has_permission(request, self) or 'ELDER' in user_roles or 'TEACHER' in user_roles):
            return Response({"detail": "생활소식/심방기록 삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
