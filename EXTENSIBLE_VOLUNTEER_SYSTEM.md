# 확장 가능한 교회별 봉사 역할 시스템 🎉

## 📝 구현 완료 내용

### 🔄 기존 시스템에서 변경된 점

**AS-IS (고정된 사역 유형)**
- `MinistryRole.MinistryType`: 하드코딩된 16개 사역 유형
- 모든 교회가 동일한 사역 유형 사용
- 새로운 사역 추가 시 코드 수정 필요

**TO-BE (확장 가능한 봉사 역할)**
- `VolunteerRole`: 교회별로 자유롭게 정의 가능한 봉사 역할
- 각 교회마다 고유한 봉사 체계 구축
- 기본 템플릿 제공 + 맞춤형 추가 가능

### 🏗️ 새로운 아키텍처

```
교회A: 아동부교사, 청년부리더, 찬양팀원, 미디어팀
교회B: 유아부담당, 중고등부멘토, 워십리더, 카페팀, 주차팀  
교회C: 새가족환영팀, 전도팀, 상담팀, 행정팀
```

### 🗃️ 새로운 데이터 모델

#### 1. VolunteerRole (봉사 역할 정의)
```python
class VolunteerRole(models.Model):
    church = models.ForeignKey(Church)           # 교회별 격리
    name = models.CharField()                    # "아동부 교사"
    code = models.CharField()                    # "children_teacher"
    description = models.TextField()             # 역할 설명
    category = models.CharField()                # 부서사역/예배사역/돌봄사역 등
    required_level = models.CharField()          # 누구나/교인만/경험자/훈련이수자
    requires_training = models.BooleanField()    # 교육 필수 여부
    training_requirements = models.TextField()   # 교육 요구사항
    target_groups = models.ManyToManyField()     # 담당 그룹들
    default_permissions = models.JSONField()     # 기본 권한 목록
    max_assignees = models.IntegerField()        # 최대 임명 인원
```

#### 2. VolunteerAssignment (봉사 할당)
```python
class VolunteerAssignment(models.Model):
    church_user = models.ForeignKey(ChurchUser)     # 할당 대상
    volunteer_role = models.ForeignKey(VolunteerRole) # 봉사 역할
    custom_permissions = models.JSONField()         # 개별 추가 권한
    start_date/end_date = models.DateField()        # 임기
    approved_by = models.ForeignKey(User)           # 승인자
    approved_at = models.DateTimeField()            # 승인 시각
```

### 🎯 10개 카테고리 & 5단계 자격 요구사항

**봉사 카테고리:**
- 부서 사역 (department)
- 예배 사역 (worship) 
- 교육 사역 (education)
- 돌봄 사역 (care)
- 전도/선교 사역 (outreach)
- 시설 관리 (facility)
- 미디어/기술 (media)
- 행정 업무 (administration)
- 특별 사역 (special)
- 기타 (other)

**자격 요구사항:**
- 누구나 (anyone)
- 교인만 (member)
- 경험자 (experienced)
- 훈련 이수자 (trained)
- 임명된 자 (appointed)

### 🔧 8개 기본 템플릿 제공

```python
DEFAULT_VOLUNTEER_ROLES = [
    {
        'name': '아동부 교사',
        'code': 'children_teacher',
        'category': 'department',
        'required_level': 'member',
        'requires_training': True,
        'training_requirements': '아동 교육 기초 과정 이수',
        'default_permissions': [
            'member.view.own_group',
            'member.update.own_group',
            'attendance.create.own_group',
            'prayer.view.own_group',
            'education.manage.own_group'
        ]
    },
    # ... 청년부리더, 셀리더, 찬양팀, 미디어팀 등
]
```

### 🚀 API 엔드포인트

#### VolunteerRoleViewSet
```bash
# 봉사 역할 관리
GET    /api/v1/churches/{id}/volunteering/roles/
POST   /api/v1/churches/{id}/volunteering/roles/
PUT    /api/v1/churches/{id}/volunteering/roles/{id}/

# 템플릿 기능
GET    /api/v1/churches/{id}/volunteering/roles/templates/
POST   /api/v1/churches/{id}/volunteering/roles/create_from_template/

# 유틸리티
GET    /api/v1/churches/{id}/volunteering/roles/categories/
GET    /api/v1/churches/{id}/volunteering/roles/required_levels/
GET    /api/v1/churches/{id}/volunteering/roles/statistics/
```

#### VolunteerAssignmentViewSet
```bash
# 봉사 할당 관리
GET    /api/v1/churches/{id}/volunteering/assignments/
POST   /api/v1/churches/{id}/volunteering/assignments/
PATCH  /api/v1/churches/{id}/volunteering/assignments/{id}/

# 특별 기능
GET    /api/v1/churches/{id}/volunteering/assignments/my_assignments/
PATCH  /api/v1/churches/{id}/volunteering/assignments/{id}/update_permissions/
GET    /api/v1/churches/{id}/volunteering/assignments/by_role/?role_id=1
```

### 🎮 관리 명령어

```bash
# 시스템 상태 확인
python manage.py init_volunteer_system --show-status

# 모든 교회에 기본 봉사 역할 생성
python manage.py init_volunteer_system --create-roles

# 특정 교회에만 생성
python manage.py init_volunteer_system --church TEST001 --create-roles

# 테스트 할당 생성
python manage.py init_volunteer_system --church TEST001 --test-assignment
```

### 🔒 권한 시스템 연동

기존 `DetailedPermission` 시스템과 완전 호환:
- 봉사 역할별 기본 권한 자동 할당
- 개별 사용자별 추가 권한 부여 가능
- 범위별 권한 (own/own_group/all) 지원

### 📊 Admin 인터페이스

```python
@admin.register(VolunteerRole)
class VolunteerRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'church', 'category_display', 'current_assignees_count']
    list_filter = ['church', 'category', 'required_level', 'is_active']
    filter_horizontal = ['target_groups']

@admin.register(VolunteerAssignment) 
class VolunteerAssignmentAdmin(admin.ModelAdmin):
    list_display = ['church_user_name', 'volunteer_role_name', 'approved_by']
    list_filter = ['volunteer_role__church', 'is_active', 'approved_by']
```

## 🌟 사용 시나리오

### 시나리오 1: 새로운 교회 셋업
```python
# 1. 기본 8개 템플릿으로 시작
POST /api/v1/churches/1/volunteering/roles/create_from_template/
{
    "template_codes": ["children_teacher", "youth_leader", "cell_leader"]
}

# 2. 교회 특화 역할 추가
POST /api/v1/churches/1/volunteering/roles/
{
    "name": "카페 봉사팀",
    "code": "cafe_team", 
    "category": "facility",
    "required_level": "anyone"
}
```

### 시나리오 2: 봉사자 임명
```python
# 1. 아동부 교사로 임명
POST /api/v1/churches/1/volunteering/assignments/
{
    "church_user": 5,
    "volunteer_role": 2,
    "start_date": "2025-01-01",
    "notes": "1학년 1반 담당"
}

# 2. 개별 권한 추가
PATCH /api/v1/churches/1/volunteering/assignments/10/update_permissions/
{
    "custom_permissions": ["announcement.create.own_group"]
}
```

### 시나리오 3: 권한 확인
```python
# 사용자가 "member.view.own_group" 권한이 있는지 확인
assignment = VolunteerAssignment.objects.get(church_user=user, is_active=True)
has_permission = assignment.has_permission("member.view.own_group")

# 모든 권한 조회 (기본 + 개별)
all_permissions = assignment.all_permissions
```

## 🎯 핵심 장점

1. **확장성**: 교회마다 무제한 봉사 역할 정의 가능
2. **재사용성**: 8개 기본 템플릿으로 빠른 시작
3. **세밀함**: 역할별 교육요구사항, 담당그룹, 정원 설정
4. **유연성**: 기본권한 + 개별권한 조합
5. **추적성**: 승인자, 승인시각, 임기 관리
6. **호환성**: 기존 권한 시스템과 완전 연동

## 🔄 기존 코드 마이그레이션

기존 `MinistryRole`은 레거시 호환을 위해 유지하되, `VolunteerRole`과 연동:

```python
class MinistryRole(models.Model):
    volunteer_role = models.ForeignKey(VolunteerRole, null=True)
    # 기존 필드들은 volunteer_role과 자동 동기화
    
    def save(self):
        if self.volunteer_role:
            self.ministry_type = self.volunteer_role.code
            self.permissions = self.volunteer_role.default_permissions
```

이제 각 교회가 고유한 봉사 문화를 시스템에 반영할 수 있습니다! 🎉