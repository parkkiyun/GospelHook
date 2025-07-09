from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Church
from .serializers import ChurchSerializer
from church_core.permissions import IsChurchMember, IsPastor

class ChurchViewSet(viewsets.ModelViewSet):
    """
    교회(Church)에 대한 API ViewSet
    - 특정 church_id에 해당하는 교회 정보 조회, 수정, 삭제
    - 교회 생성은 관리자만 가능하도록 제한
    """
    queryset = Church.objects.all()
    serializer_class = ChurchSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_queryset(self):
        # 관리자는 모든 교회를 볼 수 있도록 허용
        if self.request.user.is_superuser:
            return self.queryset
        # 일반 사용자는 자신의 교회만 볼 수 있도록 필터링
        return self.queryset.filter(id=self.kwargs.get('church_id'))

    def retrieve(self, request, *args, **kwargs):
        # URL의 church_id와 요청 사용자의 church_id가 일치하는지 확인
        # IsChurchMember 권한에서 이미 처리되므로, 여기서는 추가 로직 불필요
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # IsChurchMember 권한에서 이미 처리되므로, 여기서는 추가 로직 불필요
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # IsChurchMember 권한에서 이미 처리되므로, 여기서는 추가 로직 불필요
        return super().destroy(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # 교회 생성은 슈퍼유저 또는 PASTOR 역할만 가능하도록 제한
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "교회 생성 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)
