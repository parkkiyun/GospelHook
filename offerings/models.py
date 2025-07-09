from django.db import models

class Offering(models.Model):
    class OfferingType(models.TextChoices):
        TITHE = 'TITHE', '십일조'
        THANKSGIVING = 'THANKSGIVING', '감사헌금'
        MISSION = 'MISSION', '선교헌금'
        BUILDING = 'BUILDING', '건축헌금'
        ETC = 'ETC', '기타헌금'

    church = models.ForeignKey('church.Church', on_delete=models.CASCADE, verbose_name='소속 교회')
    member = models.ForeignKey('members.Member', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='교인 (익명 가능)')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='금액')
    offering_type = models.CharField(max_length=20, choices=OfferingType.choices, verbose_name='헌금 종류')
    date = models.DateField(verbose_name='헌금일')
    recorded_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='기록자')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '헌금 기록'
        verbose_name_plural = '헌금 기록'
        ordering = ['-date']

    def __str__(self):
        return f'{self.member.name if self.member else "익명"} - {self.amount} ({self.get_offering_type_display()})'