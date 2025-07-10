from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from church.models import Church
from volunteering.models import VolunteerRole, VolunteerAssignment, DEFAULT_VOLUNTEER_ROLES
from users.models import ChurchUser, DetailedPermission

User = get_user_model()


class Command(BaseCommand):
    help = '확장 가능한 봉사 역할 시스템을 초기화합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--church', type=str, help='특정 교회 코드 지정')
        parser.add_argument('--create-roles', action='store_true', help='기본 봉사 역할 생성')
        parser.add_argument('--test-assignment', action='store_true', help='테스트 할당 생성')
        parser.add_argument('--show-status', action='store_true', help='시스템 상태 확인')

    def handle(self, *args, **options):
        church_code = options.get('church')
        
        if church_code:
            try:
                church = Church.objects.get(code=church_code)
                self.stdout.write(f'🏛️ 대상 교회: {church.name} ({church.code})')
            except Church.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ 교회를 찾을 수 없습니다: {church_code}')
                )
                return
        else:
            church = None

        if options['create_roles']:
            self.create_default_roles(church)
        
        if options['test_assignment']:
            self.create_test_assignment(church)
        
        if options['show_status'] or not any([
            options['create_roles'], 
            options['test_assignment']
        ]):
            self.show_system_status(church)

    def create_default_roles(self, church=None):
        """기본 봉사 역할 생성"""
        if church:
            churches = [church]
        else:
            churches = Church.objects.all()
            
        if not churches:
            self.stdout.write(self.style.ERROR('❌ 교회가 없습니다. 먼저 교회를 생성해주세요.'))
            return

        created_total = 0
        
        for church in churches:
            self.stdout.write(f'\n🏛️ {church.name} 교회 봉사 역할 생성 중...')
            created_count = 0
            
            for role_data in DEFAULT_VOLUNTEER_ROLES:
                code = role_data['code']
                
                # 중복 검사
                if VolunteerRole.objects.filter(church=church, code=code).exists():
                    self.stdout.write(f'  ⚠️ 이미 존재: {role_data["name"]}')
                    continue
                
                # 역할 생성
                try:
                    volunteer_role = VolunteerRole.objects.create(
                        church=church,
                        name=role_data['name'],
                        code=role_data['code'],
                        category=role_data['category'],
                        description=role_data['description'],
                        required_level=role_data['required_level'],
                        requires_training=role_data['requires_training'],
                        training_requirements=role_data.get('training_requirements', ''),
                        default_permissions=role_data['default_permissions'],
                        created_by=None  # 시스템 생성
                    )
                    
                    created_count += 1
                    created_total += 1
                    
                    self.stdout.write(
                        f'  ✅ 생성: {volunteer_role.name} '
                        f'({volunteer_role.get_category_display()}) '
                        f'- {len(volunteer_role.default_permissions)}개 권한'
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ 생성 실패: {role_data["name"]} - {str(e)}')
                    )
            
            self.stdout.write(f'  📊 {church.name}: {created_count}개 역할 생성됨')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 총 {created_total}개 봉사 역할이 생성되었습니다!')
        )

    def create_test_assignment(self, church=None):
        """테스트 봉사 할당 생성"""
        if not church:
            try:
                church = Church.objects.first()
                if not church:
                    self.stdout.write(self.style.ERROR('❌ 교회가 없습니다.'))
                    return
            except:
                self.stdout.write(self.style.ERROR('❌ 교회를 찾을 수 없습니다.'))
                return
        
        self.stdout.write(f'\n🧪 {church.name} 교회 테스트 할당 생성 중...')
        
        # 테스트 사용자 찾기 또는 생성
        try:
            test_user = User.objects.filter(username__startswith='test').first()
            if not test_user:
                test_user = User.objects.create_user(
                    username='test_volunteer',
                    email='test@example.com',
                    password='testpass123'
                )
                self.stdout.write('👤 테스트 사용자 생성됨')
            
            church_user, created = ChurchUser.objects.get_or_create(
                user=test_user,
                church=church,
                defaults={
                    'name': '김봉사',
                    'role': 'member',
                    'phone': '010-1234-5678'
                }
            )
            if created:
                self.stdout.write('🏛️ 교회 사용자 생성됨')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 사용자 생성 실패: {str(e)}'))
            return
        
        # 봉사 역할 찾기
        volunteer_roles = VolunteerRole.objects.filter(church=church, is_active=True)[:3]
        if not volunteer_roles:
            self.stdout.write(self.style.WARNING('⚠️ 봉사 역할이 없습니다. 먼저 --create-roles를 실행하세요.'))
            return
        
        # 할당 생성
        created_assignments = 0
        for role in volunteer_roles:
            # 중복 검사
            if VolunteerAssignment.objects.filter(
                church_user=church_user, 
                volunteer_role=role
            ).exists():
                continue
            
            try:
                assignment = VolunteerAssignment.objects.create(
                    church_user=church_user,
                    volunteer_role=role,
                    notes=f'{role.name} 테스트 할당',
                    approved_by=test_user,
                    approved_at=timezone.now()
                )
                
                created_assignments += 1
                self.stdout.write(
                    f'  ✅ 할당: {church_user.name} → {role.name} '
                    f'({len(assignment.all_permissions)}개 권한)'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ 할당 실패: {role.name} - {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎯 {created_assignments}개 테스트 할당이 생성되었습니다!')
        )

    def show_system_status(self, church=None):
        """시스템 상태 표시"""
        self.stdout.write('\n📊 확장 가능한 봉사 역할 시스템 상태')
        self.stdout.write('=' * 60)
        
        if church:
            churches = [church]
            self.stdout.write(f'🎯 대상: {church.name} 교회')
        else:
            churches = Church.objects.all()
            self.stdout.write(f'🌐 전체 교회: {churches.count()}개')
        
        total_roles = 0
        total_assignments = 0
        total_permissions = DetailedPermission.objects.count()
        
        self.stdout.write(f'\n🔑 등록된 세부 권한: {total_permissions}개')
        
        for church_obj in churches:
            roles = VolunteerRole.objects.filter(church=church_obj)
            assignments = VolunteerAssignment.objects.filter(
                volunteer_role__church=church_obj,
                is_active=True
            )
            
            total_roles += roles.count()
            total_assignments += assignments.count()
            
            if len(churches) > 1:
                self.stdout.write(f'\n🏛️ {church_obj.name}:')
                self.stdout.write(f'   📋 봉사 역할: {roles.count()}개')
                self.stdout.write(f'   👥 활성 할당: {assignments.count()}개')
                
                # 카테고리별 역할 수
                categories = roles.values('category').distinct()
                for cat in categories:
                    cat_roles = roles.filter(category=cat['category'])
                    cat_display = dict(VolunteerRole.RoleCategory.choices)[cat['category']]
                    self.stdout.write(f'     - {cat_display}: {cat_roles.count()}개')
        
        self.stdout.write(f'\n📈 전체 통계:')
        self.stdout.write(f'   🏛️ 교회 수: {churches.count()}개')
        self.stdout.write(f'   📋 총 봉사 역할: {total_roles}개')
        self.stdout.write(f'   👥 총 활성 할당: {total_assignments}개')
        
        # 인기 역할 TOP 5
        from django.db.models import Count
        popular_roles = VolunteerRole.objects.annotate(
            assignment_count=Count('volunteer_assignments')
        ).order_by('-assignment_count')[:5]
        
        if popular_roles:
            self.stdout.write(f'\n🏆 인기 봉사 역할 TOP 5:')
            for i, role in enumerate(popular_roles, 1):
                self.stdout.write(
                    f'   {i}. {role.name} ({role.church.name}) - {role.assignment_count}명'
                )
        
        # 시스템 특징
        self.stdout.write(f'\n✨ 시스템 특징:')
        self.stdout.write(f'   🔧 교회별 맞춤형 봉사 역할 정의')
        self.stdout.write(f'   📝 역할별 권한 자동 할당')
        self.stdout.write(f'   🎯 담당 그룹 지정 가능')
        self.stdout.write(f'   📊 교육 요구사항 관리')
        self.stdout.write(f'   👑 승인 프로세스 지원')
        
        # 사용 방법
        self.stdout.write(f'\n💡 사용법:')
        self.stdout.write(f'   --church CODE --create-roles: 특정 교회에 기본 역할 생성')
        self.stdout.write(f'   --church CODE --test-assignment: 테스트 할당 생성')
        self.stdout.write(f'   --show-status: 전체 시스템 상태 확인')
        
        if total_roles == 0:
            self.stdout.write(f'\n🚀 시작하기: python manage.py init_volunteer_system --create-roles')


# 타임존 import 추가
from django.utils import timezone