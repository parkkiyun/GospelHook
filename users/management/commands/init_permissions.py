from django.core.management.base import BaseCommand
from users.models import DetailedPermission, DEFAULT_PERMISSIONS


class Command(BaseCommand):
    help = '기본 세부 권한 데이터를 초기화합니다.'

    def handle(self, *args, **options):
        created_count = 0
        
        for permission_data in DEFAULT_PERMISSIONS:
            code, name, category, level, scope = permission_data
            
            permission, created = DetailedPermission.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': category,
                    'level': level,
                    'scope': scope,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'권한 생성: {permission.name} ({permission.code})')
                )
            else:
                self.stdout.write(f'이미 존재함: {permission.name} ({permission.code})')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n총 {created_count}개의 새로운 권한이 생성되었습니다.')
        )