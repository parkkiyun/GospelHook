from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class BibleVersion(models.Model):
    """성경 버전 모델"""
    
    name = models.CharField(max_length=100, verbose_name='성경 번역본명')
    code = models.CharField(max_length=20, unique=True, verbose_name='코드')
    language = models.CharField(max_length=50, default='한국어', verbose_name='언어')
    description = models.TextField(blank=True, verbose_name='설명')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    
    class Meta:
        db_table = 'bible_versions'
        verbose_name = '성경 번역본'
        verbose_name_plural = '성경 번역본들'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class BibleBook(models.Model):
    """성경 책 모델"""
    
    class Testament(models.TextChoices):
        OLD = 'old', '구약'
        NEW = 'new', '신약'
    
    name = models.CharField(max_length=50, verbose_name='책명')
    code = models.CharField(max_length=10, unique=True, verbose_name='책 코드')
    testament = models.CharField(
        max_length=10, 
        choices=Testament.choices, 
        verbose_name='구분'
    )
    order = models.IntegerField(verbose_name='순서')
    chapter_count = models.IntegerField(verbose_name='장 수')
    description = models.TextField(blank=True, verbose_name='설명')
    
    class Meta:
        db_table = 'bible_books'
        verbose_name = '성경 책'
        verbose_name_plural = '성경 책들'
        ordering = ['order']
    
    def __str__(self):
        return self.name


class BibleVerse(models.Model):
    """성경 구절 모델"""
    
    version = models.ForeignKey(
        BibleVersion,
        on_delete=models.CASCADE,
        related_name='verses',
        verbose_name='번역본'
    )
    book = models.ForeignKey(
        BibleBook,
        on_delete=models.CASCADE,
        related_name='verses',
        verbose_name='책'
    )
    chapter = models.IntegerField(verbose_name='장')
    verse = models.IntegerField(verbose_name='절')
    text = models.TextField(verbose_name='본문')
    
    class Meta:
        db_table = 'bible_verses'
        verbose_name = '성경 구절'
        verbose_name_plural = '성경 구절들'
        unique_together = [['version', 'book', 'chapter', 'verse']]
        ordering = ['book__order', 'chapter', 'verse']
        indexes = [
            models.Index(fields=['book', 'chapter']),
            models.Index(fields=['version', 'book', 'chapter']),
        ]
    
    def __str__(self):
        return f"{self.book.name} {self.chapter}:{self.verse}"
    
    @property
    def reference(self):
        """성경 참조 문자열"""
        return f"{self.book.name} {self.chapter}:{self.verse}"


class SermonScripture(models.Model):
    """설교 본문 모델"""
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='sermon_scriptures',
        verbose_name='교회'
    )
    title = models.CharField(max_length=200, verbose_name='설교 제목')
    preacher = models.CharField(max_length=100, verbose_name='설교자')
    date = models.DateField(verbose_name='설교 날짜')
    
    # 본문 구절들
    main_scripture = models.CharField(
        max_length=200,
        verbose_name='주 본문',
        help_text='예: 요한복음 3:16'
    )
    sub_scriptures = models.TextField(
        blank=True,
        verbose_name='부 본문',
        help_text='여러 본문을 줄바꿈으로 구분'
    )
    
    # 설교 내용
    summary = models.TextField(blank=True, verbose_name='설교 요약')
    outline = models.TextField(blank=True, verbose_name='설교 개요')
    notes = models.TextField(blank=True, verbose_name='비고')
    
    # 파일 업로드
    audio_file = models.FileField(
        upload_to='sermons/audio/',
        null=True,
        blank=True,
        verbose_name='음성 파일'
    )
    video_file = models.FileField(
        upload_to='sermons/video/',
        null=True,
        blank=True,
        verbose_name='영상 파일'
    )
    document_file = models.FileField(
        upload_to='sermons/documents/',
        null=True,
        blank=True,
        verbose_name='설교 원고'
    )
    
    # 예배 정보
    service_type = models.CharField(
        max_length=50,
        default='주일예배',
        verbose_name='예배 종류'
    )
    
    # 시스템 필드
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sermons',
        verbose_name='등록자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'sermon_scriptures'
        verbose_name = '설교 본문'
        verbose_name_plural = '설교 본문들'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['church', 'date']),
            models.Index(fields=['preacher', 'date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.preacher} ({self.date})"
    
    def get_sub_scriptures_list(self):
        """부 본문 리스트 반환"""
        if self.sub_scriptures:
            return [s.strip() for s in self.sub_scriptures.split('\n') if s.strip()]
        return []


class DailyVerse(models.Model):
    """일일 성경 구절 모델"""
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='daily_verses',
        verbose_name='교회'
    )
    date = models.DateField(verbose_name='날짜')
    verse = models.ForeignKey(
        BibleVerse,
        on_delete=models.CASCADE,
        related_name='daily_selections',
        verbose_name='성경 구절'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='제목'
    )
    meditation = models.TextField(
        blank=True,
        verbose_name='묵상'
    )
    prayer = models.TextField(
        blank=True,
        verbose_name='기도문'
    )
    
    # 시스템 필드
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_daily_verses',
        verbose_name='등록자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'daily_verses'
        verbose_name = '일일 성경 구절'
        verbose_name_plural = '일일 성경 구절들'
        unique_together = [['church', 'date']]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.church.name} - {self.date} ({self.verse.reference})"


class BibleStudy(models.Model):
    """성경 공부 모델"""
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='bible_studies',
        verbose_name='교회'
    )
    title = models.CharField(max_length=200, verbose_name='제목')
    description = models.TextField(blank=True, verbose_name='설명')
    
    # 성경 공부 범위
    start_book = models.ForeignKey(
        BibleBook,
        on_delete=models.CASCADE,
        related_name='study_starts',
        verbose_name='시작 책'
    )
    start_chapter = models.IntegerField(verbose_name='시작 장')
    start_verse = models.IntegerField(verbose_name='시작 절')
    
    end_book = models.ForeignKey(
        BibleBook,
        on_delete=models.CASCADE,
        related_name='study_ends',
        verbose_name='마지막 책'
    )
    end_chapter = models.IntegerField(verbose_name='마지막 장')
    end_verse = models.IntegerField(verbose_name='마지막 절')
    
    # 일정 정보
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(null=True, blank=True, verbose_name='종료일')
    
    # 그룹 정보
    leader = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        related_name='leading_bible_studies',
        verbose_name='인도자'
    )
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bible_studies',
        verbose_name='대상 그룹'
    )
    
    # 상태
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')
    
    # 시스템 필드
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_bible_studies',
        verbose_name='등록자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'bible_studies'
        verbose_name = '성경 공부'
        verbose_name_plural = '성경 공부들'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} ({self.start_date})"
    
    @property
    def reference_range(self):
        """성경 공부 범위 문자열"""
        if self.start_book == self.end_book:
            if self.start_chapter == self.end_chapter:
                return f"{self.start_book.name} {self.start_chapter}:{self.start_verse}-{self.end_verse}"
            else:
                return f"{self.start_book.name} {self.start_chapter}:{self.start_verse}-{self.end_chapter}:{self.end_verse}"
        else:
            return f"{self.start_book.name} {self.start_chapter}:{self.start_verse} - {self.end_book.name} {self.end_chapter}:{self.end_verse}"


class BibleBookmark(models.Model):
    """성경 책갈피 모델"""
    
    church = models.ForeignKey(
        'church.Church',
        on_delete=models.CASCADE,
        related_name='bible_bookmarks',
        verbose_name='교회'
    )
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='bible_bookmarks',
        verbose_name='교인'
    )
    verse = models.ForeignKey(
        BibleVerse,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name='성경 구절'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='제목'
    )
    note = models.TextField(
        blank=True,
        verbose_name='메모'
    )
    color = models.CharField(
        max_length=7,
        default='#ffff00',
        verbose_name='색상',
        help_text='HEX 색상 코드'
    )
    
    # 시스템 필드
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'bible_bookmarks'
        verbose_name = '성경 책갈피'
        verbose_name_plural = '성경 책갈피들'
        unique_together = [['member', 'verse']]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.member.name} - {self.verse.reference}"