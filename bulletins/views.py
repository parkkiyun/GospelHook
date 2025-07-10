from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date, timedelta
from .models import Bulletin
from .serializers import BulletinListSerializer, BulletinDetailSerializer, BulletinCreateSerializer
from church_core.unified_permissions import UnifiedPermission


class BulletinViewSet(viewsets.ModelViewSet):
    """주보 관리 API ViewSet"""
    resource_name = 'bulletin'
    queryset = Bulletin.objects.all()
    permission_classes = [IsAuthenticated, UnifiedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date']
    search_fields = ['title']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        """교회별 주보 필터링"""
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == 'list':
            return BulletinListSerializer
        elif self.action in ['create']:
            return BulletinCreateSerializer
        return BulletinDetailSerializer

    def perform_create(self, serializer):
        """주보 생성 시 교회 정보 자동 설정"""
        church_id = self.kwargs.get('church_id')
        serializer.save(church_id=church_id, created_by=self.request.user)

    # create, update, destroy는 기본적으로 UnifiedPermission에서 처리됩니다.
    # 특정 권한(예: bulletin.create)이 있는 사용자만 해당 작업을 수행할 수 있습니다.
    # 교회 관리자는 모든 권한을 가집니다.

    @action(detail=False, methods=['get'])
    def recent(self, request, church_id=None):
        """최근 주보 목록 (최근 30일)"""
        recent_date = date.today() - timedelta(days=30)
        queryset = self.get_queryset().filter(date__gte=recent_date)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def latest(self, request, church_id=None):
        """최신 주보"""
        latest_bulletin = self.get_queryset().first()
        if latest_bulletin:
            serializer = BulletinDetailSerializer(
                latest_bulletin, context={'request': request}
            )
            return Response(serializer.data)
        return Response({"detail": "주보가 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def by_year(self, request, church_id=None):
        """연도별 주보 목록"""
        year = request.query_params.get('year')
        if not year:
            return Response(
                {"detail": "연도를 지정해주세요."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
            queryset = self.get_queryset().filter(date__year=year)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"detail": "올바른 연도를 입력해주세요."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
