from django.contrib import admin
from django.db.models import Count

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Отображение ингредиентов и поиск по названию в админ-панели."""

    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 0
    min_num = 1
    validate_min = True
    fields = ('ingredient', 'measurement_unit', 'amount')
    readonly_fields = ('measurement_unit',)

    @admin.display(description='Ед. изм.')
    def measurement_unit(self, obj):
        ingredient = getattr(obj, 'ingredient', None)
        return getattr(ingredient, 'measurement_unit', '')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Отображение рецептов и фильтрация по тегам в админке."""

    list_display = ('id', 'name', 'author', 'favorites_count')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    readonly_fields = ('favorites_count',)
    inlines = (IngredientInRecipeInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(favorites_count=Count('in_favorites'))

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return getattr(obj, 'favorites_count', obj.in_favorites.count())


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Отображение ингредиентов с количеством внутри рецепта в админке."""

    list_display = ('id', 'recipe', 'ingredient', 'measurement_unit', 'amount')
    list_display_links = ('id', 'recipe')

    @admin.display(description='Ед. изм.')
    def measurement_unit(self, obj):
        ingredient = getattr(obj, 'ingredient', None)
        return getattr(ingredient, 'measurement_unit', '')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Отображение и поиск тегов в админке."""

    list_display = ('id', 'name', 'slug')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'slug')
    ordering = ('name',)


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
