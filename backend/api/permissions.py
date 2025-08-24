from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Права доступа только для администраторов."""

    def has_permission(self, request, view):
        """Проверяет, является ли пользователь администратором."""
        user = request.user
        return bool(user and user.is_authenticated and (getattr(user, 'is_admin', False) or user.is_superuser))


class IsAuthorOrReadOnly(BasePermission):
    """
    Права доступа для пользователя (автор), администратора или только чтение.
    """

    def has_permission(self, request, view):
        """Проверяет права на уровне запроса."""
        return request.method in SAFE_METHODS or (request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """
        Проверяет права на уровне объекта.
        """
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(
            (hasattr(obj, 'author') and obj.author == user)
            or getattr(user, 'is_admin', False)
            or user.is_superuser
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Права доступа только для админа или только чтение.
    """

    def has_permission(self, request, view):
        """Проверяет права на уровне запроса для админа или только чтение."""
        user = request.user
        return request.method in SAFE_METHODS or (
            user and user.is_authenticated and (getattr(user, 'is_admin', False) or user.is_superuser)
        )
