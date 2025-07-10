# 권한 시스템 통합 재설계 계획

## 🎯 목표
- 역할(MinistryRole)을 봉사(VolunteerRole)로 통합
- 봉사와 그룹을 연결하여 효율적인 권한 관리
- 일관성 있고 단순한 권한 로직 구현

## 📋 현재 문제점
1. **중복 시스템**: MinistryRole ↔ VolunteerRole/VolunteerAssignment
2. **복잡한 권한 체크**: 3가지 다른 권한 시스템 공존
3. **일관성 부족**: ViewSet마다 다른 권한 검증 방식
4. **유지보수 어려움**: 레거시와 신규 시스템 혼재

## 🔄 통합 설계

### 1. 새로운 권한 모델 구조

```
ChurchUser (교회 사용자)
├── role: 기본 역할 (admin, staff, member)
└── VolunteerAssignment (봉사 할당) - 핵심!
    ├── VolunteerRole (봉사 역할 정의)
    ├── target_groups (담당 그룹들)
    ├── permissions (개별 권한)
    └── scope (권한 범위: own, group, all)
```

### 2. 권한 계층 구조

```
1. 시스템 권한: 슈퍼유저, 교회 관리자
2. 봉사 기반 권한: VolunteerAssignment를 통한 세부 권한
3. 그룹 기반 권한: 담당 그룹에 대한 권한
4. 개인 권한: 본인 데이터에 대한 권한
```

### 3. 통합 권한 로직

```python
class UnifiedPermission:
    def has_permission(self, user, action, resource, obj=None):
        # 1. 시스템 권한 확인
        if user.is_superuser:
            return True
            
        # 2. 교회 관리자 권한 확인
        church_user = get_church_user(user, obj)
        if church_user.is_admin:
            return True
            
        # 3. 봉사 기반 권한 확인
        for assignment in church_user.volunteer_assignments.active():
            if assignment.has_permission(action, resource, obj):
                return True
                
        return False
```

## 🚀 구현 단계

### Phase 1: 새로운 권한 시스템 구축
1. VolunteerAssignment 모델 확장
2. 통합 권한 검증 클래스 구현
3. 권한 매핑 시스템 구축

### Phase 2: ViewSet 권한 통합
1. 모든 ViewSet에 통합 권한 적용
2. 기존 권한 로직 교체
3. API 테스트 및 검증

### Phase 3: 레거시 시스템 제거
1. MinistryRole 모델 삭제
2. DetailedPermission 모델 삭제  
3. 기존 permissions.py, ministry_permissions.py 정리

### Phase 4: 최적화 및 정리
1. 권한 캐싱 시스템 구현
2. Admin 인터페이스 개선
3. 문서화 및 테스트 보완

## 💡 주요 개선 사항

### 1. 단순화된 권한 구조
- 하나의 권한 시스템으로 통합
- 직관적인 봉사 기반 권한 관리
- 그룹과 봉사의 자연스러운 연결

### 2. 효율적인 권한 검증
- 단일 권한 검증 포인트
- 캐싱을 통한 성능 최적화
- 명확한 권한 범위 정의

### 3. 유지보수성 향상
- 일관된 코드 구조
- 중복 코드 제거
- 명확한 권한 로직

## 📊 마이그레이션 전략

### 데이터 마이그레이션
1. 기존 MinistryRole → VolunteerAssignment 변환
2. 기존 권한 데이터 보존 및 이전
3. 단계적 데이터 검증

### 호환성 유지
1. 기존 API 호환성 보장
2. 점진적 시스템 교체
3. 롤백 계획 수립

이 계획대로 진행하면 권한 시스템이 훨씬 간단하고 효율적으로 변할 것입니다!