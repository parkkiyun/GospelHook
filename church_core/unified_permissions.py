"""
통합 권한 시스템 - 모든 권한 체크를 하나로 통합
"""
from rest_framework import permissions
from django.core.cache import cache
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class UnifiedPermission(permissions.BasePermission):
    """
    통합 권한 시스템 - 봉사 기반 권한 관리

    권한 계층:
    1. 시스템 권한: 슈퍼유저
    2. 교회 관리자 권한: church_admin
    3. 교회 스태프 권한: church_staff (일부 관리 기능)
    4. 봉사 기반 권한: VolunteerAssignment를 통한 세부 권한
    5. 그룹 기반 권한: 담당 그룹에 대한 권한
    6. 개인 권한: 본인 데이터에 대한 권한
    """

    def has_permission(self, request, view):
        """뷰 레벨 권한 체크"""
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        church_id = self._get_church_id(request, view)
        if not church_id:
            # 교회 컨텍스트가 없는 API는 개별적으로 처리
            return True 

        church_user = self._get_church_user(request.user, church_id)
        if not church_user or not church_user.is_active:
            return False

        # 교회 관리자/스태프는 대부분의 뷰에 접근 가능
        if church_user.is_admin or church_user.is_staff:
            return True

        # 뷰에 필요한 기본 권한 확인
        required_permission = self._get_required_permission(view, request.method)
        if not required_permission:
            return True  # 특정 권한이 필요 없는 뷰

        return self._has_volunteer_permission(church_user, required_permission)

    def has_object_permission(self, request, view, obj):
        """객체 레벨 권한 체크"""
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        church_id = self._get_church_id_from_object(obj)
        if not church_id:
            return False

        church_user = self._get_church_user(request.user, church_id)
        if not church_user or not church_user.is_active:
            return False

        if church_user.is_admin:
            return True

        required_permission = self._get_required_permission(view, request.method)
        if not required_permission:
            return True

        return self._has_volunteer_object_permission(church_user, required_permission, obj)

    def _get_church_id(self, request, view):
        """요청에서 교회 ID 추출"""
        return view.kwargs.get('church_id')

    def _get_church_id_from_object(self, obj):
        """객체에서 교회 ID 추출"""
        if hasattr(obj, 'church_id'):
            return obj.church_id
        elif hasattr(obj, 'church'):
            return obj.church.id if obj.church else None
        # 다른 모델들과의 관계를 통해 church_id를 찾는 로직 추가
        elif hasattr(obj, 'member') and hasattr(obj.member, 'church'):
            return obj.member.church.id
        elif hasattr(obj, 'program') and hasattr(obj.program, 'church'):
            return obj.program.church.id
        return None

    def _get_church_user(self, user, church_id):
        """사용자의 교회별 정보 조회 (캐싱)"""
        cache_key = f"church_user_{user.id}_{church_id}"
        church_user = cache.get(cache_key)
        if church_user is None:
            try:
                church_user = user.church_users.select_related('church').get(
                    church_id=church_id, is_active=True
                )
                cache.set(cache_key, church_user, 300)  # 5분 캐싱
            except user.church_users.model.DoesNotExist:
                church_user = None
        return church_user

    def _get_required_permission(self, view, method):
        """뷰와 HTTP 메서드에 따른 필요 권한 문자열 생성"""
        resource_name = getattr(view, 'resource_name', None)
        if not resource_name:
            return None

        action_map = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        action = action_map.get(method, 'view')
        return f"{resource_name}.{action}"

    def _has_volunteer_permission(self, church_user, permission_base):
        """사용자가 특정 기본 권한을 가지고 있는지 확인 (뷰 레벨)"""
        # 활성 봉사 할당 조회 (캐싱 고려)
        assignments = self._get_user_assignments(church_user)
        
        for assignment in assignments:
            # .all, .own_group, .own 등 모든 범위를 허용
            if any(p.startswith(permission_base) for p in assignment.all_permissions):
                return True
        return False

    def _has_volunteer_object_permission(self, church_user, permission_base, obj):
        """봉사 기반 객체 권한 확인"""
        assignments = self._get_user_assignments(church_user)

        for assignment in assignments:
            permissions = assignment.all_permissions
            
            # 전체 권한
            if f"{permission_base}.all" in permissions or f"{self._get_resource_from_permission(permission_base)}.manage.all" in permissions:
                return True

            # 그룹 권한
            if f"{permission_base}.own_group" in permissions or f"{self._get_resource_from_permission(permission_base)}.manage.own_group" in permissions:
                if self._is_group_data(obj, assignment):
                    return True
            
            # 개인 권한
            if f"{permission_base}.own" in permissions:
                if self._is_own_data(obj, church_user):
                    return True
        
        return False

    def _get_user_assignments(self, church_user):
        """사용자의 활성 봉사 할당 목록 조회 (캐싱)"""
        cache_key = f"volunteer_assignments_{church_user.id}"
        assignments = cache.get(cache_key)
        if assignments is None:
            assignments = list(church_user.volunteer_assignments.filter(
                is_active=True
            ).select_related('volunteer_role').prefetch_related('volunteer_role__target_groups'))
            cache.set(cache_key, assignments, 300)
        return assignments

    def _is_own_data(self, obj, church_user):
        """본인 데이터인지 확인"""
        if hasattr(obj, 'created_by') and obj.created_by == church_user.user:
            return True
        if hasattr(obj, 'user') and obj.user == church_user.user:
            return True
        if hasattr(obj, 'member') and hasattr(obj.member, 'user') and obj.member.user == church_user.user:
            return True
        return False

    def _is_group_data(self, obj, assignment):
        """담당 그룹의 데이터인지 확인"""
        target_groups = assignment.volunteer_role.target_groups.all()
        if not target_groups.exists():
            return False

        if hasattr(obj, 'group') and obj.group in target_groups:
            return True
        
        if hasattr(obj, 'member') and obj.member.groups.filter(pk__in=target_groups.values('pk')).exists():
            return True

        if hasattr(obj, 'groups') and obj.groups.filter(pk__in=target_groups.values('pk')).exists():
            return True

        return False
    
    def _get_resource_from_permission(self, permission_base):
        return permission_base.split('.')[0]


# 편의 클래스
class ReadOnly(UnifiedPermission):
    def has_permission(self, request, view):
        if request.method not in permissions.SAFE_METHODS:
            return False
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return False
        return super().has_object_permission(request, view, obj)
