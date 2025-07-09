from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # 기본 username, password, email 등은 AbstractUser에 포함되어 있음
    
    class Role(models.TextChoices):
        PASTOR = 'PASTOR', '교역자'
        ELDER = 'ELDER', '구역장'
        TEACHER = 'TEACHER', '교사'
        MEMBER = 'MEMBER', '성도'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        verbose_name='직책'
    )

    church = models.ForeignKey(
        'church.Church', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='소속 교회'
    )

    related_member = models.OneToOneField(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='연결된 교인 정보'
    )

    def __str__(self):
        return self.username