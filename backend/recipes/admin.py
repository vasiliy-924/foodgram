from django.contrib import admin

from recipes.models import IngredientInRecipe, Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Отображение рецептов и фильтрация по тегам в админке."""

    list_display = ('id', 'name', 'author')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Отображение ингредиентов с количеством внутри рецепта в админке."""
    
    list_display = ('id', 'recipe', 'ingredient', 'amount')
