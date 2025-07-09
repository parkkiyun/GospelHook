from django.db import models

class Group(models.Model):
    class GroupType(models.TextChoices):
        DEPARTMENT = 'DEPARTMENT', '부서'
        DISTRICT = 'DISTRICT', '구역'
        CHOIR = 'CHOIR', '찬양대'
        ETC = 'ETC', '기타'

    class ManagementType(models.TextChoices):
        AUTO = 'AUTO', '자동'
        MANUAL = 'MANUAL', '수동'

    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    name = models.CharField(max_length=100, verbose_name='그룹 이름')
    group_type = models.CharField(max_length=20, choices=GroupType.choices, verbose_name='그룹 종류')
    management_type = models.CharField(max_length=10, choices=ManagementType.choices, default=ManagementType.MANUAL, verbose_name='관리 유형')
    age_min = models.PositiveIntegerField(null=True, blank=True, verbose_name='최소 연령')
    age_max = models.PositiveIntegerField(null=True, blank=True, verbose_name='최대 연령')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name