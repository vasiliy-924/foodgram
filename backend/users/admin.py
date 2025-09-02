from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для модели User."""

    list_display = (
        'first_name', 'last_name', 'username',
        'email', 'avatar'
    )
    list_display_links = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            'Дополнительно',
            {
                'fields': (
                    'avatar',
                )
            }
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username', 'password1', 'password2',
                    'email', 'first_name', 'last_name',
                    'avatar',
                ),
            },
        ),
    )
