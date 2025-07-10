from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from datetime import date
from .models import (
    BibleVersion, BibleBook, BibleVerse, SermonScripture,
    DailyVerse, BibleStudy, BibleBookmark
)
from .serializers import (
    BibleVersionSerializer, BibleBookSerializer, BibleVerseSerializer,
    BibleVerseSearchSerializer, SermonScriptureSerializer, SermonScriptureListSerializer,
    DailyVerseSerializer, BibleStudySerializer, BibleStudyListSerializer,
    BibleBookmarkSerializer, BibleBookmarkCreateSerializer
)
from church_core.roles import SystemRole, Permission
from users.models import ChurchUser


class BibleVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """성경 번역본 ViewSet"""
    queryset = BibleVersion.objects.filter(is_active=True)
    serializer_class = BibleVersionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'language']
    ordering = ['name']


class BibleBookViewSet(viewsets.ReadOnlyModelViewSet):
    """성경 책 ViewSet"""
    queryset = BibleBook.objects.all()
    serializer_class = BibleBookSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['testament']
    search_fields = ['name', 'code']
    ordering = ['order']


class BibleVerseViewSet(viewsets.ReadOnlyModelViewSet):
    """성경 구절 ViewSet"""
    queryset = BibleVerse.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['version', 'book', 'chapter']
    search_fields = ['text']
    ordering = ['book__order', 'chapter', 'verse']
    
    def get_serializer_class(self):
        if self.action == 'search':
            return BibleVerseSearchSerializer
        return BibleVerseSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """성경 구절 검색"""
        keyword = request.query_params.get('q', '')
        if not keyword:
            return Response({"detail": "검색어를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(text__icontains=keyword)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BibleVerseSearchSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BibleVerseSearchSerializer(queryset, many=True)
        return Response(serializer.data)


class SermonScriptureViewSet(viewsets.ModelViewSet):
    """설교 본문 ViewSet"""
    queryset = SermonScripture.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['preacher', 'service_type']
    search_fields = ['title', 'preacher', 'main_scripture', 'summary']
    ordering = ['-date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SermonScriptureListSerializer
        return SermonScriptureSerializer
    
    def get_queryset(self):
        user = self.request.user
        church_id = self.kwargs.get('church_id')
        
        if user.is_superuser:
            queryset = self.queryset
        else:
            user_churches = user.church_users.values_list('church', flat=True)
            queryset = self.queryset.filter(church__in=user_churches)
        
        if church_id:
            queryset = queryset.filter(church_id=church_id)
        
        return queryset
    
    def perform_create(self, serializer):
        church_id = self.kwargs.get('church_id')
        church_user = self.request.user.church_users.filter(church_id=church_id).first()
        
        if church_user:
            serializer.save(
                church=church_user.church,
                created_by=self.request.user
            )
        else:
            serializer.save(created_by=self.request.user)


class DailyVerseViewSet(viewsets.ModelViewSet):
    """일일 성경 구절 ViewSet"""
    queryset = DailyVerse.objects.all()
    serializer_class = DailyVerseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date']
    ordering = ['-date']
    
    def get_queryset(self):
        user = self.request.user
        church_id = self.kwargs.get('church_id')
        
        if user.is_superuser:
            queryset = self.queryset
        else:
            user_churches = user.church_users.values_list('church', flat=True)
            queryset = self.queryset.filter(church__in=user_churches)
        
        if church_id:
            queryset = queryset.filter(church_id=church_id)
        
        return queryset
    
    def perform_create(self, serializer):
        church_id = self.kwargs.get('church_id')
        church_user = self.request.user.church_users.filter(church_id=church_id).first()
        
        if church_user:
            serializer.save(
                church=church_user.church,
                created_by=self.request.user
            )
        else:
            serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """오늘의 말씀"""
        today = date.today()
        church_id = self.kwargs.get('church_id')
        
        daily_verse = self.get_queryset().filter(date=today).first()
        if daily_verse:
            serializer = self.get_serializer(daily_verse)
            return Response(serializer.data)
        
        return Response({"detail": "오늘의 말씀이 등록되지 않았습니다."}, status=status.HTTP_404_NOT_FOUND)


class BibleStudyViewSet(viewsets.ModelViewSet):
    """성경 공부 ViewSet"""
    queryset = BibleStudy.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'leader', 'group']
    search_fields = ['title', 'description']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BibleStudyListSerializer
        return BibleStudySerializer
    
    def get_queryset(self):
        user = self.request.user
        church_id = self.kwargs.get('church_id')
        
        if user.is_superuser:
            queryset = self.queryset
        else:
            user_churches = user.church_users.values_list('church', flat=True)
            queryset = self.queryset.filter(church__in=user_churches)
        
        if church_id:
            queryset = queryset.filter(church_id=church_id)
        
        return queryset
    
    def perform_create(self, serializer):
        church_id = self.kwargs.get('church_id')
        church_user = self.request.user.church_users.filter(church_id=church_id).first()
        
        if church_user:
            serializer.save(
                church=church_user.church,
                created_by=self.request.user
            )
        else:
            serializer.save(created_by=self.request.user)


class BibleBookmarkViewSet(viewsets.ModelViewSet):
    """성경 책갈피 ViewSet"""
    queryset = BibleBookmark.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['member', 'color']
    search_fields = ['title', 'note', 'verse__text']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BibleBookmarkCreateSerializer
        return BibleBookmarkSerializer
    
    def get_queryset(self):
        user = self.request.user
        church_id = self.kwargs.get('church_id')
        
        if user.is_superuser:
            queryset = self.queryset
        else:
            user_churches = user.church_users.values_list('church', flat=True)
            queryset = self.queryset.filter(church__in=user_churches)
        
        if church_id:
            queryset = queryset.filter(church_id=church_id)
        
        return queryset
    
    def perform_create(self, serializer):
        church_id = self.kwargs.get('church_id')
        church_user = self.request.user.church_users.filter(church_id=church_id).first()
        
        if church_user:
            serializer.save(church=church_user.church)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def my_bookmarks(self, request):
        """내 책갈피 조회"""
        user = request.user
        church_id = self.kwargs.get('church_id')
        
        try:
            from members.models import Member
            member = Member.objects.get(user=user, church_id=church_id)
            bookmarks = self.get_queryset().filter(member=member)
            
            page = self.paginate_queryset(bookmarks)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(bookmarks, many=True)
            return Response(serializer.data)
            
        except Member.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)