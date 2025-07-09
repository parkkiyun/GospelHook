from django.db import models

class Attendance(models.Model):
    class AttendanceStatus(models.TextChoices):
        PRESENT = 'PRESENT', '출석'
        ABSENT = 'ABSENT', '결석'
        LATE = 'LATE', '지각'
        ETC = 'ETC', '기타'

    class WorshipType(models.TextChoices):
        SUNDAY = 'SUNDAY', '주일예배'
        WEDNESDAY = 'WEDNESDAY', '수요예배'
        FRIDAY = 'FRIDAY', '금요철야'
        DAWN = 'DAWN', '새벽예배'
        SPECIAL = 'SPECIAL', '특별집회'
        ETC = 'ETC', '기타'

    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, verbose_name='교인')
    date = models.DateField(verbose_name='날짜')
    status = models.CharField(max_length=10, choices=AttendanceStatus.choices, verbose_name='상태')
    worship_type = models.CharField(max_length=20, choices=WorshipType.choices, verbose_name='예배 종류')
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='기록자')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('member', 'date', 'worship_type') # 한 교인은 특정 날짜, 특정 예배에 한 번만 출석 기록
        verbose_name = '출석'
        verbose_name_plural = '출석'

    def __str__(self):
        return f'{self.member.name} - {self.date} - {self.get_status_display()}'