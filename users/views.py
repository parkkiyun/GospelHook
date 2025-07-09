from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer, UserCreateSerializer
from church_core.permissions import IsChurchMember

class UserViewSet(viewsets.ModelViewSet):
    """
    사용자(User)에 대한 API ViewSet
    - 슈퍼유저는 모든 사용자 관리 가능
    - 일반 사용자는 자신의 정보만 조회/수정 가능
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        # 슈퍼유저는 모든 사용자를 볼 수 있음
        if self.request.user.is_superuser:
            return self.queryset
        # 일반 사용자는 자신의 교회에 속한 사용자만 볼 수 있음
        return self.queryset.filter(church=self.request.user.church)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 슈퍼유저가 아니면서 자신의 정보가 아니면 접근 불가
        if not request.user.is_superuser and instance != request.user:
            return Response({"detail": "접근 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # 슈퍼유저가 아니면서 자신의 정보가 아니면 수정 불가
        if not request.user.is_superuser and instance != request.user:
            return Response({"detail": "수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 슈퍼유저가 아니면서 자신의 정보가 아니면 삭제 불가
        if not request.user.is_superuser and instance != request.user:
            return Response({"detail": "삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # 사용자 생성은 슈퍼유저만 가능하도록 제한
        if not request.user.is_superuser:
            return Response({"detail": "사용자 생성 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)
