from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import ChurchUser, MinistryRole, DetailedPermission
from church.models import Church
from groups.models import Group
from church_core.ministry_permissions import assign_ministry_permissions

User = get_user_model()


class Command(BaseCommand):
    help = '사역 기반 권한 시스템을 테스트합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--create-test-data', action='store_true', help='테스트 데이터 생성')
        parser.add_argument('--test-permissions', action='store_true', help='권한 시스템 테스트')

    def handle(self, *args, **options):
        if options['create_test_data']:
            self.create_test_data()
        
        if options['test_permissions']:
            self.test_permissions()
        
        if not any(options.values()):
            self.show_system_status()

    def create_test_data(self):
        """테스트 데이터 생성"""
        self.stdout.write('🔨 테스트 데이터 생성 중...')
        
        # 교회 생성
        church, created = Church.objects.get_or_create(
            name='테스트교회',
            defaults={
                'code': 'TEST001',
                'address': '서울시 강남구',
                'phone': '02-1234-5678',
                'timezone': 'Asia/Seoul'
            }
        )
        if created:
            self.stdout.write(f'✅ 교회 생성: {church.name}')
        
        # 사용자 및 교회 사용자 생성
        user, created = User.objects.get_or_create(
            username='teacher01',
            defaults={
                'email': 'teacher01@test.com',
                'first_name': '김',
                'last_name': '선생'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'✅ 사용자 생성: {user.username}')
        
        church_user, created = ChurchUser.objects.get_or_create(
            user=user,
            church=church,
            defaults={
                'name': '김선생',
                'role': 'member',
                'phone': '010-1234-5678'
            }
        )
        if created:
            self.stdout.write(f'✅ 교회 사용자 생성: {church_user.name}')
        
        # 그룹 생성
        group, created = Group.objects.get_or_create(
            church=church,
            name='1학년 1반',
            defaults={
                'group_type': 'department',
                'description': '초등학교 1학년 1반',
                'age_min': 7,
                'age_max': 8,
                'management_type': 'auto'
            }
        )
        if created:
            self.stdout.write(f'✅ 그룹 생성: {group.name}')
        
        # 사역 역할 생성
        ministry_role, created = MinistryRole.objects.get_or_create(
            church_user=church_user,
            ministry_type='children_teacher',
            defaults={
                'notes': '1학년 1반 담당 교사'
            }
        )
        if created:
            ministry_role.target_groups.add(group)
            assign_ministry_permissions(ministry_role)
            self.stdout.write(f'✅ 사역 역할 생성: {ministry_role.get_ministry_type_display()}')
        
        self.stdout.write(self.style.SUCCESS('✨ 테스트 데이터 생성 완료!'))

    def test_permissions(self):
        """권한 시스템 테스트"""
        self.stdout.write('🔍 권한 시스템 테스트 중...')
        
        # 아동부 교사 찾기
        try:
            ministry_role = MinistryRole.objects.filter(
                ministry_type='children_teacher'
            ).first()
            
            if not ministry_role:
                self.stdout.write(self.style.ERROR('❌ 아동부 교사 역할을 찾을 수 없습니다.'))
                return
            
            self.stdout.write(f'👤 테스트 대상: {ministry_role.church_user.name} ({ministry_role.get_ministry_type_display()})')
            
            # 권한 테스트
            permissions_to_test = [
                'member.view.own_group',
                'attendance.create.own_group', 
                'prayer.view.own_group',
                'education.manage.own_group',
                'member.view.all'  # 이건 없어야 함
            ]
            
            for permission in permissions_to_test:
                has_permission = ministry_role.has_permission(permission)
                status = '✅' if has_permission else '❌'
                self.stdout.write(f'{status} {permission}: {has_permission}')
            
            # 담당 그룹 확인
            target_groups = ministry_role.target_groups.all()
            self.stdout.write(f'📋 담당 그룹: {[g.name for g in target_groups]}')
            
            # 전체 권한 목록
            self.stdout.write(f'🔑 보유 권한 ({len(ministry_role.permissions)}개):')
            for perm in ministry_role.permissions:
                self.stdout.write(f'   - {perm}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 권한 테스트 실패: {e}'))

    def show_system_status(self):
        """시스템 상태 표시"""
        self.stdout.write('📊 사역 기반 권한 시스템 상태')
        self.stdout.write('=' * 50)
        
        # 기본 통계
        permission_count = DetailedPermission.objects.count()
        ministry_role_count = MinistryRole.objects.count()
        active_ministry_count = MinistryRole.objects.filter(is_active=True).count()
        
        self.stdout.write(f'📝 등록된 세부 권한: {permission_count}개')
        self.stdout.write(f'👥 전체 사역 역할: {ministry_role_count}개')
        self.stdout.write(f'✅ 활성 사역 역할: {active_ministry_count}개')
        
        # 사역 유형별 통계
        self.stdout.write('\n📈 사역 유형별 현황:')
        ministry_types = MinistryRole.objects.values_list('ministry_type', flat=True).distinct()
        for ministry_type in ministry_types:
            count = MinistryRole.objects.filter(ministry_type=ministry_type, is_active=True).count()
            display_name = dict(MinistryRole.MinistryType.choices).get(ministry_type, ministry_type)
            self.stdout.write(f'   - {display_name}: {count}명')
        
        # 권한 카테고리별 통계
        self.stdout.write('\n🏷️ 권한 카테고리별 현황:')
        categories = DetailedPermission.objects.values_list('category', flat=True).distinct()
        for category in categories:
            count = DetailedPermission.objects.filter(category=category).count()
            display_name = dict(DetailedPermission.PermissionCategory.choices).get(category, category)
            self.stdout.write(f'   - {display_name}: {count}개')
        
        self.stdout.write('\n💡 사용법:')
        self.stdout.write('  --create-test-data: 테스트 데이터 생성')
        self.stdout.write('  --test-permissions: 권한 시스템 테스트')
        self.stdout.write('\n🔧 관련 명령어:')
        self.stdout.write('  python manage.py init_permissions  # 기본 권한 초기화')