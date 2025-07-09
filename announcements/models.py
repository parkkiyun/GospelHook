from django.db import models

class Announcement(models.Model):
    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    visible_roles = models.JSONField(default=list, blank=True, verbose_name='가시 직책 (JSON 배열)') # 예: ["PASTOR", "MEMBER"]
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='작성자')
    push_enabled = models.BooleanField(default=False, verbose_name='푸시 알림 활성화')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '공지사항'
        verbose_name_plural = '공지사항'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class PushLog(models.Model):
    class PushStatus(models.TextChoices):
        SENT = 'SENT', '발송됨'
        FAILED = 'FAILED', '실패'
        READ = 'READ', '읽음'

    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, verbose_name='공지사항')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='수신 사용자')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='발송 시각')
    status = models.CharField(max_length=10, choices=PushStatus.choices, default=PushStatus.SENT, verbose_name='상태')

    class Meta:
        verbose_name = '푸시 알림 로그'
        verbose_name_plural = '푸시 알림 로그'
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.announcement.title} to {self.user.username} - {self.get_status_display()}'
