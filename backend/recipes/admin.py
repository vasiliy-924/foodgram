from django.contrib import admin
from django.db.models import Count

from recipes.models import IngredientInRecipe, Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Отображение рецептов и фильтрация по тегам в админке."""

    list_display = ('id', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    readonly_fields = ('favorites_count',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(favorites_count=Count('in_favorites'))

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return getattr(obj, 'favorites_count', obj.in_favorites.count())


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Отображение ингредиентов с количеством внутри рецепта в админке."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
