from django.db import models

class CareLog(models.Model):
    class CareLogType(models.TextChoices):
        PRAYER = 'PRAYER', '기도'
        NEWS = 'NEWS', '생활소식'
        HOSPITAL_VISIT = 'HOSPITAL_VISIT', '병문안'
        ETC = 'ETC', '기타'

    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, verbose_name='교인')
    type = models.CharField(max_length=20, choices=CareLogType.choices, verbose_name='기록 유형')
    content = models.TextField(verbose_name='내용')
    date = models.DateField(verbose_name='기록일')
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='작성자')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '생활소식/심방기록'
        verbose_name_plural = '생활소식/심방기록'
        ordering = ['-date']

    def __str__(self):
        return f'{self.member.name} - {self.get_type_display()} - {self.date}'