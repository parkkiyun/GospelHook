from rest_framework.routers import DefaultRouter
from .views import MemberViewSet, FamilyRelationshipViewSet, FamilyTreeViewSet

router = DefaultRouter()
router.register(r'', MemberViewSet, basename='member')
router.register(r'family-relationships', FamilyRelationshipViewSet, basename='family-relationship')
router.register(r'family-trees', FamilyTreeViewSet, basename='family-tree')

urlpatterns = router.urls