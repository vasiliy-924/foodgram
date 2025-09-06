from django.contrib import admin
from django.db.models import Count
from django.utils.safestring import mark_safe

from foodgram_backend.constants import (
    ADMIN_INGREDIENT_INLINE_EXTRA,
    ADMIN_INGREDIENT_INLINE_MIN_NUM,
    ADMIN_RECIPE_IMAGE_HEIGHT,
    ADMIN_RECIPE_IMAGE_WIDTH,
)
from recipes.filters import CookingTimeFilter
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
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
    extra = ADMIN_INGREDIENT_INLINE_EXTRA
    min_num = ADMIN_INGREDIENT_INLINE_MIN_NUM
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

    list_display = (
        'id',
        'name',
        'image_tag',
        'author',
        'tags_list',
        'ingredients_list',
        'favorites_count',
    )
    list_display_links = ('id', 'name')
    search_fields = ('name', 'author__username')
    list_filter = ('tags', CookingTimeFilter)
    readonly_fields = ('favorites_count',)
    inlines = (IngredientInRecipeInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.annotate(favorites_count=Count('favorite')).prefetch_related(
                'tags', 'ingredients'
            )
        )

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return getattr(obj, 'favorites_count', obj.favorite_set.count())

    @admin.display(description='Теги')
    def tags_list(self, obj):
        return ', '.join(obj.tags.values_list('name', flat=True))

    @admin.display(description='Ингредиенты')
    def ingredients_list(self, obj):
        return ', '.join(obj.ingredients.values_list('name', flat=True))

    @admin.display(description='Картинка')
    def image_tag(self, obj):
        return mark_safe(
            f'<img src={obj.image.url} width="{ADMIN_RECIPE_IMAGE_WIDTH}" '
            f'height="{ADMIN_RECIPE_IMAGE_HEIGHT}">'
        )


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
