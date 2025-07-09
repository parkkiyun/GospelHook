from django.db import models

class WorshipRecord(models.Model):
    class WorshipType(models.TextChoices):
        SUNDAY = 'SUNDAY', '주일예배'
        WEDNESDAY = 'WEDNESDAY', '수요예배'
        FRIDAY = 'FRIDAY', '금요철야'
        DAWN = 'DAWN', '새벽예배'
        SPECIAL = 'SPECIAL', '특별집회'
        ETC = 'ETC', '기타'

    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    date = models.DateField(verbose_name='예배일')
    worship_type = models.CharField(max_length=20, choices=WorshipType.choices, verbose_name='예배 종류')
    preacher = models.CharField(max_length=100, verbose_name='설교자')
    theme = models.CharField(max_length=200, blank=True, verbose_name='설교 주제')
    scripture = models.CharField(max_length=200, blank=True, verbose_name='성경 구절')
    attendees = models.ManyToManyField('members.Member', blank=True, verbose_name='참석 교인')
    summary = models.TextField(blank=True, verbose_name='요약')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '예배 기록'
        verbose_name_plural = '예배 기록'
        ordering = ['-date']

    def __str__(self):
        return f'{self.get_worship_type_display()} - {self.date} - {self.preacher}'