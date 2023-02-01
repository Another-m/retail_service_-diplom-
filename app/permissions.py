from rest_framework import permissions

from app.models import UserInfo


class IsSupplier(permissions.BasePermission):
    def has_permission(self, request, view):
        obj = UserInfo.objects.filter(user__username=request.user).first()
        c_type = obj.company.counterparty_type
        if c_type == 'supplier':
            return True
        return False
