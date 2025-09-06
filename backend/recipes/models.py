from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from foodgram_backend.constants import (
    INGREDIENT_NAME_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH,
    MIN_COOKING_TIME_MINUTES,
    MIN_INGREDIENT_AMOUNT,
    RECIPE_NAME_MAX_LENGTH,
    SLUG_MAX_LENGTH,
    STR_REPRESENTATION_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH
)


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_name_unit'
            ),
        )

    def __str__(self):
        """Возвращает отображаемое имя ингредиента."""
        return self.name[:STR_REPRESENTATION_MAX_LENGTH]


class Tag(models.Model):
    """Модель тега рецепта."""

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        """Возвращает отображаемое имя тега."""
        return self.name[:STR_REPRESENTATION_MAX_LENGTH]


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    created_at = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=(MinValueValidator(MIN_COOKING_TIME_MINUTES),)
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at', '-id')

    def __str__(self):
        """Возвращает отображаемое название рецепта."""
        return self.name[:STR_REPRESENTATION_MAX_LENGTH]


class IngredientInRecipe(models.Model):
    """Ингредиент внутри рецепта с количеством."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipes',
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipes',
        verbose_name='Рецепт'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=(MinValueValidator(MIN_INGREDIENT_AMOUNT),)
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_per_recipe'
            ),
        )

    def __str__(self):
        """Возвращает отображаемое имя ингредиента в рецепте."""
        return self.ingredient[:STR_REPRESENTATION_MAX_LENGTH]


class UserRecipeRelation(models.Model):
    """Абстрактная связь пользователя и рецепта (избранное/покупки)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True

    def __str__(self):
        """Уникальная строка за счет включения типа связи."""
        text = f"{self._meta.verbose_name}: {self.recipe}"
        return text[:STR_REPRESENTATION_MAX_LENGTH]


class Favorite(UserRecipeRelation):
    """Связь рецепта и пользователя в списке избранного."""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_per_user'
            ),
        )


class ShoppingCart(UserRecipeRelation):
    """Позиция рецепта в списке покупок пользователя."""

    class Meta:
        verbose_name = 'Позиция в списке покупок'
        verbose_name_plural = 'Список покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_cart_item_per_user'
            ),
        )
