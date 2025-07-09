from rest_framework import viewsets
from .models import Offering
from .serializers import OfferingSerializer

class OfferingViewSet(viewsets.ModelViewSet):
    """
    헌금 기록(Offering)에 대한 API ViewSet
    """
    queryset = Offering.objects.all()
    serializer_class = OfferingSerializer

    def get_queryset(self):
        """
        URL의 church_id를 기반으로 해당 교회의 헌금 기록만 필터링합니다.
        """
        church_id = self.kwargs.get('church_id')
        return self.queryset.filter(church_id=church_id)