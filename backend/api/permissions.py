from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """Права доступа для автора, администратора или только чтение."""

    def has_permission(self, request, view):
        """Проверяет права на уровне запроса."""
        return request.method in SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Проверяет права на уровне объекта.
        """
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
            or request.user.is_superuser
        )
