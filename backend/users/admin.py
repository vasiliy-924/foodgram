from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count

from users.models import Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для модели User."""

    list_display = (
        'first_name', 'last_name', 'username',
        'email', 'avatar',
        'recipes_count', 'subscribers_count'
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            recipes_count=Count('recipes', distinct=True),
            subscribers_count=Count('subscriptions_to_author', distinct=True),
        )

    @admin.display(description='Рецептов', ordering='recipes_count')
    def recipes_count(self, obj):
        return obj.recipes_count

    @admin.display(description='Подписчиков', ordering='subscribers_count')
    def subscribers_count(self, obj):
        return obj.subscribers_count


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Отображение подписок пользователей на авторов в админке."""

    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
