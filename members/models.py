from django.db import models

class Member(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', '남성'
        FEMALE = 'F', '여성'

    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    name = models.CharField(max_length=50, verbose_name='이름')
    gender = models.CharField(max_length=1, choices=Gender.choices, null=True, blank=True, verbose_name='성별')
    birth_date = models.DateField(null=True, blank=True, verbose_name='생년월일')
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True, verbose_name='프로필 사진')
    group = models.ForeignKey('groups.Group', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='소속 그룹')
    
    is_active = models.BooleanField(default=True, verbose_name='활성 교인')
    auto_group_enabled = models.BooleanField(default=True, verbose_name='자동 진급 대상')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name