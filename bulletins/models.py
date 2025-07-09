from django.db import models

class Bulletin(models.Model):
    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    title = models.CharField(max_length=200, verbose_name='제목')
    file = models.FileField(upload_to='bulletins/', verbose_name='주보 파일 (PDF)')
    date = models.DateField(verbose_name='발행일')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '주보'
        verbose_name_plural = '주보'
        ordering = ['-date']

    def __str__(self):
        return f'{self.title} ({self.date})'