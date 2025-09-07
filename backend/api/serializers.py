from django.contrib.auth import get_user_model
from django.db.models import Count
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.services import build_absolute_file_url
from foodgram_backend.constants import (
    MIN_COOKING_TIME_MINUTES,
    MIN_INGREDIENT_AMOUNT,
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import Subscription


User = get_user_model()


# Пользователи:
class SetAvatarSerializer(serializers.Serializer):
    """Сериализатор установки аватара пользователя из base64-строки."""

    avatar = Base64ImageField(required=True)

    def save(self, **kwargs):
        """Декодирует base64 и сохраняет аватар текущего пользователя."""
        user = self.context['request'].user
        avatar_file = self.validated_data['avatar']
        user.avatar = avatar_file
        user.save(update_fields=['avatar'])
        return user

    def create(self, validated_data):
        """Возвращает валидированные данные без создания объектов."""
        return validated_data

    def update(self, instance, validated_data):
        """Не изменяет объект и возвращает переданный экземпляр."""
        return instance


class UserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя для чтения данных профиля."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = tuple(dict.fromkeys(
            DjoserUserSerializer.Meta.fields + ('is_subscribed', 'avatar')
        ))
        read_only_fields = tuple(dict.fromkeys(getattr(
            DjoserUserSerializer.Meta,
            'read_only_fields',
            ()
        ) + ('is_subscribed', 'avatar'))
        )

    def get_is_subscribed(self, obj):
        """Возвращает True, если текущий пользователь подписан на автора."""
        request = self.context.get('request')
        return bool(
            request
            and getattr(request, 'user', None)
            and request.user.is_authenticated
            and obj
            and request.user.user_subscriptions.filter(author=obj).exists()
        )

    def get_avatar(self, obj):
        """Возвращает абсолютный URL аватара пользователя."""
        request = self.context.get('request')
        return build_absolute_file_url(request, obj.avatar)


# Справочники (теги, ингредиенты)
class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id',)


# Сериализаторы рецептов

class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецепта (id, имя, изображение, время)."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id',)

    def get_image(self, obj):
        """Возвращает абсолютный URL изображения рецепта."""
        request = self.context.get('request')
        return build_absolute_file_url(request, obj.image)


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента в составе рецепта (чтение)."""

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAmountWriteSerializer(serializers.Serializer):
    """Элемент списка ингредиентов при создании/редактировании рецепта."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для чтения."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True, source='ingredient_in_recipes', read_only=True
    )
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True,
        default=False,
    )
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id',)

    def get_image(self, obj):
        """Возвращает абсолютный URL изображения рецепта."""
        request = self.context.get('request')
        return build_absolute_file_url(request, obj.image)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для записи (создание/обновление)."""

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientAmountWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME_MINUTES
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'tags', 'image', 'name',
            'text', 'cooking_time'
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        """Валидирует ингредиенты, теги и время готовки."""
        request = self.context.get('request')
        is_full_update = bool(
            request and getattr(request, 'method', '').upper() == 'PUT'
        )

        method = (getattr(request, 'method', '') if request else '').upper()
        initial = self.initial_data or {}
        image_value = initial.get('image', None)
        if (
            (method == 'POST' and image_value in (None, ''))
            or (
                method in ('PUT', 'PATCH')
                and 'image' in initial
                and image_value in (None, '')
            )
        ):
            raise serializers.ValidationError(
                {'image': ['Обязательное поле.']})

        required_fields = (
            'ingredients', 'tags', 'name', 'text', 'cooking_time'
        )

        if is_full_update:
            missing = [
                f for f in required_fields if f not in self.initial_data
            ]
            if missing:
                raise serializers.ValidationError({
                    f: ['Обязательное поле.'] for f in missing
                })

        ingredients = attrs.get('ingredients', None)
        tags = attrs.get('tags', None)

        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': ['Обязательное поле.']
            })
        ingredient_ids = [item['id'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': ['Ингредиент не должен повторяться.']
            })

        if not tags:
            raise serializers.ValidationError({'tags': ['Обязательное поле.']})
        tags_input = self.initial_data.get('tags')
        if isinstance(tags_input, (list, tuple)) and (
            len(tags_input) != len(set(tags_input))
        ):
            raise serializers.ValidationError({
                'tags': ['Теги не должны повторяться.']
            })
        return attrs

    @staticmethod
    def _set_ingredients(recipe, ingredients):
        """Создает список ингредиентов рецепта из переданного списка."""
        IngredientInRecipe.objects.bulk_create(
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=item['id'].id,
                amount=item['amount'],
            )
            for item in ingredients
        )

    def create(self, validated_data):
        """Создает рецепт, устанавливает теги и ингредиенты."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет поля рецепта, теги и/или ингредиенты."""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if tags:
            instance.tags.set(tags)
        elif tags is not None:
            instance.tags.set([])
        if ingredients:
            IngredientInRecipe.objects.filter(recipe=instance).delete()
            self._set_ingredients(instance, ingredients)
        elif ingredients is not None:
            IngredientInRecipe.objects.filter(recipe=instance).delete()
        return instance

    def to_representation(self, instance):
        """Возвращает представление через сериализатор чтения рецепта."""
        return RecipeReadSerializer(instance, context=self.context).data


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с его рецептами и их количеством."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = tuple(getattr(UserSerializer.Meta, 'fields', ())) + (
            'recipes', 'recipes_count'
        )
        read_only_fields = tuple(set(getattr(
            UserSerializer.Meta,
            'read_only_fields',
            ()
        ) + ('recipes', 'recipes_count'))
        )

    def get_recipes(self, obj):
        """Возвращает рецепты автора; учитывает параметр recipes_limit."""
        request = self.context.get('request')
        limit = None
        if request:
            try:
                raw_limit = request.query_params.get('recipes_limit')
                limit = int(raw_limit) if raw_limit is not None else None
            except Exception:
                limit = None
        qs = obj.recipes.all()
        qs = qs[:limit]
        return RecipeMinifiedSerializer(
            qs,
            many=True,
            context={'request': request}
        ).data


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания подписки пользователя на автора."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        """Запрещает подписку на себя и повторную подписку."""
        user = attrs.get('user')
        author = attrs.get('author')

        if user == author:
            raise serializers.ValidationError({
                'detail': 'Нельзя подписаться на себя.'
            })

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError({
                'detail': 'Подписка уже существует.'
            })

        return attrs

    def create(self, validated_data):
        return Subscription.objects.create(**validated_data)

    def to_representation(self, instance):
        """Возвращает данные автора подписки как в списке подписок."""
        author_with_count = (
            User.objects
            .filter(pk=instance.author_id)
            .annotate(recipes_count=Count('recipes'))
            .first()
        ) or instance.author
        return UserWithRecipesSerializer(
            author_with_count,
            context=self.context,
        ).data


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецепта в избранное."""

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, attrs):
        user = attrs.get('user')
        recipe = attrs.get('recipe')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError({
                'detail': 'Уже в избранном.'
            })
        return attrs

    def create(self, validated_data):
        return Favorite.objects.create(**validated_data)

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context,
        ).data


class ShoppingCartCreateSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецепта в список покупок."""

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, attrs):
        user = attrs.get('user')
        recipe = attrs.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError({
                'detail': 'Уже в списке покупок.'
            })
        return attrs

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context,
        ).data
