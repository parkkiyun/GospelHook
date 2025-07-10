from rest_framework import serializers
from .models import (
    BibleVersion, BibleBook, BibleVerse, SermonScripture,
    DailyVerse, BibleStudy, BibleBookmark
)
from members.serializers import MemberBasicSerializer
from groups.serializers import GroupListSerializer


class BibleVersionSerializer(serializers.ModelSerializer):
    """성경 번역본 시리얼라이저"""
    
    class Meta:
        model = BibleVersion
        fields = ['id', 'name', 'code', 'language', 'description', 'is_active']


class BibleBookSerializer(serializers.ModelSerializer):
    """성경 책 시리얼라이저"""
    
    class Meta:
        model = BibleBook
        fields = ['id', 'name', 'code', 'testament', 'order', 'chapter_count', 'description']


class BibleVerseSerializer(serializers.ModelSerializer):
    """성경 구절 시리얼라이저"""
    version_name = serializers.CharField(source='version.name', read_only=True)
    book_name = serializers.CharField(source='book.name', read_only=True)
    reference = serializers.CharField(read_only=True)
    
    class Meta:
        model = BibleVerse
        fields = [
            'id', 'version', 'version_name', 'book', 'book_name',
            'chapter', 'verse', 'text', 'reference'
        ]


class BibleVerseSearchSerializer(serializers.ModelSerializer):
    """성경 구절 검색용 시리얼라이저"""
    version_name = serializers.CharField(source='version.name', read_only=True)
    book_name = serializers.CharField(source='book.name', read_only=True)
    reference = serializers.CharField(read_only=True)
    
    class Meta:
        model = BibleVerse
        fields = ['id', 'version_name', 'book_name', 'chapter', 'verse', 'reference', 'text']


class SermonScriptureListSerializer(serializers.ModelSerializer):
    """설교 본문 목록용 시리얼라이저"""
    
    class Meta:
        model = SermonScripture
        fields = [
            'id', 'title', 'preacher', 'date', 'main_scripture',
            'service_type', 'created_at'
        ]


class SermonScriptureSerializer(serializers.ModelSerializer):
    """설교 본문 시리얼라이저"""
    sub_scriptures_list = serializers.ListField(source='get_sub_scriptures_list', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = SermonScripture
        fields = [
            'id', 'title', 'preacher', 'date', 'main_scripture',
            'sub_scriptures', 'sub_scriptures_list', 'summary', 'outline',
            'notes', 'audio_file', 'video_file', 'document_file',
            'service_type', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DailyVerseSerializer(serializers.ModelSerializer):
    """일일 성경 구절 시리얼라이저"""
    verse_detail = BibleVerseSerializer(source='verse', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = DailyVerse
        fields = [
            'id', 'date', 'verse', 'verse_detail', 'title',
            'meditation', 'prayer', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BibleStudySerializer(serializers.ModelSerializer):
    """성경 공부 시리얼라이저"""
    start_book_name = serializers.CharField(source='start_book.name', read_only=True)
    end_book_name = serializers.CharField(source='end_book.name', read_only=True)
    reference_range = serializers.CharField(read_only=True)
    leader_name = serializers.CharField(source='leader.name', read_only=True)
    group_detail = GroupListSerializer(source='group', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = BibleStudy
        fields = [
            'id', 'title', 'description', 'start_book', 'start_book_name',
            'start_chapter', 'start_verse', 'end_book', 'end_book_name',
            'end_chapter', 'end_verse', 'reference_range', 'start_date',
            'end_date', 'leader', 'leader_name', 'group', 'group_detail',
            'is_active', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BibleStudyListSerializer(serializers.ModelSerializer):
    """성경 공부 목록용 시리얼라이저"""
    reference_range = serializers.CharField(read_only=True)
    leader_name = serializers.CharField(source='leader.name', read_only=True)
    
    class Meta:
        model = BibleStudy
        fields = [
            'id', 'title', 'reference_range', 'start_date', 'end_date',
            'leader_name', 'is_active'
        ]


class BibleBookmarkSerializer(serializers.ModelSerializer):
    """성경 책갈피 시리얼라이저"""
    verse_detail = BibleVerseSerializer(source='verse', read_only=True)
    member_name = serializers.CharField(source='member.name', read_only=True)
    
    class Meta:
        model = BibleBookmark
        fields = [
            'id', 'member', 'member_name', 'verse', 'verse_detail',
            'title', 'note', 'color', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BibleBookmarkCreateSerializer(serializers.ModelSerializer):
    """성경 책갈피 생성용 시리얼라이저"""
    member_id = serializers.IntegerField()
    verse_id = serializers.IntegerField()
    
    class Meta:
        model = BibleBookmark
        fields = ['member_id', 'verse_id', 'title', 'note', 'color']
    
    def validate(self, attrs):
        """유효성 검사"""
        # 멤버 존재 확인
        member_id = attrs.get('member_id')
        try:
            from members.models import Member
            member = Member.objects.get(id=member_id)
            attrs['member'] = member
        except Member.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 멤버입니다.")
        
        # 성경 구절 존재 확인
        verse_id = attrs.get('verse_id')
        try:
            verse = BibleVerse.objects.get(id=verse_id)
            attrs['verse'] = verse
        except BibleVerse.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 성경 구절입니다.")
        
        return attrs