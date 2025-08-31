from django.contrib import admin

from interactions.models import Favorite, ShoppingCart, Subscription


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Отображение избранных рецептов пользователей в админке."""

    list_display = ('user', 'recipe')
    list_display_links = ('recipe',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Отображение списка покупок пользователей в админке."""

    list_display = ('user', 'recipe')
    list_display_links = ('recipe',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Отображение подписок пользователей на авторов в админке."""

    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
