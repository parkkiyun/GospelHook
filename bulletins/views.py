from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Bulletin
from .serializers import BulletinSerializer
from church_core.permissions import IsChurchMember, IsPastor

class BulletinViewSet(viewsets.ModelViewSet):
    """
    주보(Bulletin)에 대한 API ViewSet
    """
    queryset = Bulletin.objects.all()
    serializer_class = BulletinSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 주보만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)

    def create(self, request, *args, **kwargs):
        # 주보 생성은 슈퍼유저 또는 PASTOR만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "주보 생성 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # 주보 수정은 슈퍼유저 또는 PASTOR만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "주보 수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # 주보 삭제는 슈퍼유저 또는 PASTOR만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "주보 삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
