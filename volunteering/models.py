from django.db import models

class VolunteerApplication(models.Model):
    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    title = models.CharField(max_length=200, verbose_name='봉사 제목')
    description = models.TextField(verbose_name='설명')
    date = models.DateField(verbose_name='봉사일')
    target_roles = models.JSONField(default=list, blank=True, verbose_name='대상 직책 (JSON 배열)') # 예: ["MEMBER"]
    max_people = models.PositiveIntegerField(null=True, blank=True, verbose_name='최대 인원')
    applicants = models.ManyToManyField('members.Member', blank=True, verbose_name='신청 교인')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '봉사 신청'
        verbose_name_plural = '봉사 신청'
        ordering = ['-date']

    def __str__(self):
        return self.title