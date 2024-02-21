from rest_framework import permissions


class AdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (request.user.is_authenticated and (request.user.role == 'admin'
                or request.user.is_superuser
                or request.user.is_staff))
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return False
        return True


class TitlePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_object_permission(self, request, view, obj):
        if request.method == 'GET':
            return True
        return request.user.is_authenticated and (
            request.user.is_superuser
            or request.user.is_staff
            or request.user.role == 'admin'
        )


class SuperUserOrAdminOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and (
                request.user.is_superuser
                or request.user.role == 'admin'
                or request.user.is_staff
            )
        )


class ReviewOrCommentPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated and (
                request.user.is_superuser
                or request.user.is_staff
                or request.user.role == 'admin'
                or request.user.role == 'moderator'
                or request.user == obj.author))
