from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Group
from .serializers import GroupSerializer
from church_core.permissions import IsChurchMember, IsPastor
from rolepermissions.roles import get_user_roles

class GroupViewSet(viewsets.ModelViewSet):
    """
    그룹(Group)에 대한 API ViewSet
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 그룹만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)

    def create(self, request, *args, **kwargs):
        # 그룹 생성은 슈퍼유저, PASTOR, ELDER만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self) or 'ELDER' in [role.name for role in get_user_roles(request.user)]):
            return Response({"detail": "그룹 생성 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # 그룹 수정은 슈퍼유저, PASTOR, ELDER만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self) or 'ELDER' in [role.name for role in get_user_roles(request.user)]):
            return Response({"detail": "그룹 수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # 그룹 삭제는 슈퍼유저, PASTOR, ELDER만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self) or 'ELDER' in [role.name for role in get_user_roles(request.user)]):
            return Response({"detail": "그룹 삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
