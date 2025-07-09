from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import WorshipRecord
from .serializers import WorshipRecordSerializer
from church_core.permissions import IsChurchMember, IsPastor

class WorshipRecordViewSet(viewsets.ModelViewSet):
    """
    예배 기록(WorshipRecord)에 대한 API ViewSet
    """
    queryset = WorshipRecord.objects.all()
    serializer_class = WorshipRecordSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 예배 기록만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)

    def create(self, request, *args, **kwargs):
        # 예배 기록 생성은 슈퍼유저 또는 PASTOR만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "예배 기록 생성 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # 예배 기록 수정은 슈퍼유저 또는 PASTOR만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "예배 기록 수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # 예배 기록 삭제는 슈퍼유저 또는 PASTOR만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "예배 기록 삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
