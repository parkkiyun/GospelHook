from rest_framework import permissions
from rolepermissions.roles import assign_role, get_user_roles

class IsPastor(permissions.BasePermission):
    """
    요청 사용자가 PASTOR 역할을 가지고 있는지 확인합니다.
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            roles = get_user_roles(request.user)
            return any(isinstance(role, type(view.request.user.Role.PASTOR)) for role in roles)
        return False

class IsChurchMember(permissions.BasePermission):
    """
    요청 사용자가 해당 교회의 멤버인지 확인합니다.
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            church_id = view.kwargs.get('church_id')
            if request.user.is_superuser:
                return True # 슈퍼유저는 모든 교회에 접근 가능
            return request.user.church_id == int(church_id)
        return False

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    객체의 소유자만 수정/삭제를 허용하고, 그 외는 읽기만 허용합니다.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.created_by == request.user
