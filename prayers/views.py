from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Prayer
from .serializers import PrayerSerializer
from church_core.permissions import IsChurchMember, IsPastor, IsOwnerOrReadOnly
from rolepermissions.roles import get_user_roles

class PrayerViewSet(viewsets.ModelViewSet):
    """
    기도제목(Prayer)에 대한 API ViewSet
    """
    queryset = Prayer.objects.all()
    serializer_class = PrayerSerializer
    permission_classes = [IsAuthenticated, IsChurchMember, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 기도제목만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)

    def perform_create(self, serializer):
        # 기도제목 생성 시 작성자를 자동으로 현재 사용자로 설정
        serializer.save(created_by=self.request.user, church=self.request.user.church)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # 슈퍼유저 또는 PASTOR가 아니면서 자신의 기도제목이 아니면 수정 불가
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)) and instance.created_by != request.user:
            return Response({"detail": "기도제목 수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 슈퍼유저 또는 PASTOR가 아니면서 자신의 기도제목이 아니면 삭제 불가
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)) and instance.created_by != request.user:
            return Response({"detail": "기도제목 삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
