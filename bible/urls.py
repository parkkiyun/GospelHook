from rest_framework.routers import DefaultRouter
from .views import (
    BibleVersionViewSet, BibleBookViewSet, BibleVerseViewSet,
    SermonScriptureViewSet, DailyVerseViewSet, BibleStudyViewSet,
    BibleBookmarkViewSet
)

router = DefaultRouter()
router.register(r'versions', BibleVersionViewSet, basename='bible-version')
router.register(r'books', BibleBookViewSet, basename='bible-book')
router.register(r'verses', BibleVerseViewSet, basename='bible-verse')
router.register(r'sermons', SermonScriptureViewSet, basename='sermon')
router.register(r'daily-verses', DailyVerseViewSet, basename='daily-verse')
router.register(r'studies', BibleStudyViewSet, basename='bible-study')
router.register(r'bookmarks', BibleBookmarkViewSet, basename='bible-bookmark')

urlpatterns = router.urls
