from django.urls import path
from .views import ChurchViewSet

urlpatterns = [
    path('', ChurchViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }), name='church-detail'),
]