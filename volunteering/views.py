from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import VolunteerApplication
from .serializers import VolunteerApplicationSerializer
from church_core.permissions import IsChurchMember, IsPastor

class VolunteerApplicationViewSet(viewsets.ModelViewSet):
    """
    봉사 신청(VolunteerApplication)에 대한 API ViewSet
    """
    queryset = VolunteerApplication.objects.all()
    serializer_class = VolunteerApplicationSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 봉사 신청 기록만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)

    def perform_create(self, serializer):
        # 봉사 신청 생성 시 church를 자동으로 설정
        serializer.save(church=self.request.user.church)

    def create(self, request, *args, **kwargs):
        # 봉사 신청은 인증된 모든 교인 가능
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # 슈퍼유저 또는 PASTOR가 아니면서 자신의 신청이 아니면 수정 불가
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)) and instance.applicants.filter(id=request.user.related_member.id).exists(): # Check if current user is an applicant
            return Response({"detail": "봉사 신청 수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 슈퍼유저 또는 PASTOR가 아니면서 자신의 신청이 아니면 삭제 불가
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)) and instance.applicants.filter(id=request.user.related_member.id).exists(): # Check if current user is an applicant
            return Response({"detail": "봉사 신청 삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
