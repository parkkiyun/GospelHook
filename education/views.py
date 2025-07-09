from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import EducationProgram, EducationRegistration
from .serializers import EducationProgramSerializer, EducationRegistrationSerializer
from church_core.permissions import IsChurchMember, IsPastor

class EducationProgramViewSet(viewsets.ModelViewSet):
    """
    교육 프로그램(EducationProgram)에 대한 API ViewSet
    """
    queryset = EducationProgram.objects.all()
    serializer_class = EducationProgramSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 교육 프로그램만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)

    def create(self, request, *args, **kwargs):
        # 교육 프로그램 생성은 슈퍼유저 또는 PASTOR만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "교육 프로그램 생성 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # 교육 프로그램 수정은 슈퍼유저 또는 PASTOR만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "교육 프로그램 수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # 교육 프로그램 삭제는 슈퍼유저 또는 PASTOR만 가능
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)):
            return Response({"detail": "교육 프로그램 삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

class EducationRegistrationViewSet(viewsets.ModelViewSet):
    """
    교육 신청(EducationRegistration)에 대한 API ViewSet
    """
    queryset = EducationRegistration.objects.all()
    serializer_class = EducationRegistrationSerializer
    permission_classes = [IsAuthenticated, IsChurchMember]

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 교육 신청 기록만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(program__church_id=church_id)

    def perform_create(self, serializer):
        # 교육 신청 시 신청 교인을 자동으로 현재 사용자의 related_member로 설정
        # TODO: request.user.related_member가 없을 경우 처리 필요
        serializer.save(member=self.request.user.related_member)

    def create(self, request, *args, **kwargs):
        # 교육 신청은 인증된 모든 교인 가능
        if not request.user.related_member:
            return Response({"detail": "교인 정보가 연결되지 않은 사용자입니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # 슈퍼유저 또는 PASTOR가 아니면서 자신의 신청이 아니면 수정 불가
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)) and instance.member != request.user.related_member:
            return Response({"detail": "교육 신청 수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 슈퍼유저 또는 PASTOR가 아니면서 자신의 신청이 아니면 삭제 불가
        if not (request.user.is_superuser or IsPastor().has_permission(request, self)) and instance.member != request.user.related_member:
            return Response({"detail": "교육 신청 삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
