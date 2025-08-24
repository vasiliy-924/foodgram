from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для модели User с расширенными возможностями."""

    list_display = (
        'first_name', 'last_name', 'username',
        'email', 'role', 'avatar'
    )
    list_display_links = ('username', 'email')
    