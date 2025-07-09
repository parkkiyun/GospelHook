from django.db import models

class EducationProgram(models.Model):
    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    title = models.CharField(max_length=200, verbose_name='프로그램 제목')
    description = models.TextField(verbose_name='설명')
    date = models.DateField(verbose_name='교육일')
    registration_deadline = models.DateField(verbose_name='등록 마감일')
    target_roles = models.JSONField(default=list, blank=True, verbose_name='대상 직책 (JSON 배열)') # 예: ["PASTOR", "TEACHER"]
    max_people = models.PositiveIntegerField(null=True, blank=True, verbose_name='최대 인원')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '교육 프로그램'
        verbose_name_plural = '교육 프로그램'
        ordering = ['-date']

    def __str__(self):
        return f'{self.title} ({self.date})'

class EducationRegistration(models.Model):
    class RegistrationStatus(models.TextChoices):
        APPLIED = 'APPLIED', '신청'
        ATTENDED = 'ATTENDED', '출석'
        COMPLETED = 'COMPLETED', '수료'
        CANCELED = 'CANCELED', '취소'

    program = models.ForeignKey(EducationProgram, on_delete=models.CASCADE, verbose_name='교육 프로그램')
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, verbose_name='신청 교인')
    status = models.CharField(max_length=10, choices=RegistrationStatus.choices, default=RegistrationStatus.APPLIED, verbose_name='상태')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='신청일')

    class Meta:
        unique_together = ('program', 'member') # 한 교인은 한 프로그램에 한 번만 신청 가능
        verbose_name = '교육 신청'
        verbose_name_plural = '교육 신청'

    def __str__(self):
        return f'{self.member.name} - {self.program.title} ({self.get_status_display()})'
