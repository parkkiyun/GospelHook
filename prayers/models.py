from django.db import models

class Prayer(models.Model):
    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, verbose_name='교인')
    content = models.TextField(verbose_name='기도제목 내용')
    date = models.DateField(auto_now_add=True, verbose_name='작성일')
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='작성자')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '기도제목'
        verbose_name_plural = '기도제목'
        ordering = ['-date']

    def __str__(self):
        return f'{self.member.name} - {self.content[:20]}...'