from django.db import models

class Church(models.Model):
    name = models.CharField(max_length=100, verbose_name='교회 이름')
    timezone = models.CharField(max_length=50, default='Asia/Seoul', verbose_name='시간대')
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name='교회 도메인')
    settings = models.JSONField(default=dict, verbose_name='교회별 커스텀 설정')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name