import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from api.services import build_absolute_file_url
from ingredients.models import Ingredient
from interactions.models import Favorite, ShoppingCart, Subscription
from recipes.models import IngredientInRecipe, Recipe
from tags.models import Tag


User = get_user_model()


# Пользователи:
class SetAvatarSerializer(serializers.Serializer):
    """Сериализатор установки аватара пользователя из base64-строки."""
    
    avatar = serializers.CharField(required=True)

    def save(self, **kwargs):
        """Декодирует base64 и сохраняет аватар текущего пользователя."""
        user = self.context['request'].user
        data = self.validated_data['avatar']
        if ',' in data:
            _, b64 = data.split(',', 1)
        else:
            b64 = data
        content = ContentFile(base64.b64decode(b64), name='avatar.png')
        user.avatar.save('avatar.png', content, save=True)
        return user

    def create(self, validated_data):
        """Возвращает валидированные данные без создания объектов."""
        return validated_data

    def update(self, instance, validated_data):
        """Не изменяет объект и возвращает переданный экземпляр."""
        return instance


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля текущего пользователя."""
    
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def create(self, validated_data):
        """Возвращает валидированные данные без создания объектов."""
        return validated_data

    def update(self, instance, validated_data):
        """Не изменяет объект и возвращает переданный экземпляр."""
        return instance


class TokenCreateSerializer(serializers.Serializer):
    """Сериализатор для получения токена авторизации (email + пароль)."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        """Проверяет наличие полей и корректность email + пароля."""
        email = data.get('email')
        password = data.get('password')

        errors = {}
        if not email:
            errors['email'] = ['Обязательное поле.']
        if not password:
            errors['password'] = ['Обязательное поле.']
        if errors:
            raise serializers.ValidationError(errors)

        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            raise serializers.ValidationError({
                'email': ['Неверные учетные данные.']
            })

        data['user'] = user
        return data

    def create(self, validated_data):
        """Возвращает валидированные данные без создания объектов."""
        return validated_data

    def update(self, instance, validated_data):
        """Не изменяет объект и возвращает переданный экземпляр."""
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователя."""
    
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        """Создает пользователя и сохраняет хешированный пароль."""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя для чтения данных профиля."""
    
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )
        read_only_fields = ('id', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        """Возвращает True, если текущий пользователь подписан на автора."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=obj
        ).exists()

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

class Base64ImageField(serializers.ImageField):
    """Поле изображения, принимающее и валидирующее base64-строку."""
    
    def to_internal_value(self, data):
        """Преобразует base64-строку в файл изображения."""
        if isinstance(data, str):
            if 'base64,' in data:
                _, data = data.split('base64,', 1)
            try:
                decoded_file = base64.b64decode(data)
            except Exception:
                raise serializers.ValidationError(
                    'Некорректное изображение (base64).'
                )
            file_name = 'image'
            file = ContentFile(decoded_file, name=f'{file_name}.png')
            return super().to_internal_value(file)
        return super().to_internal_value(data)


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
    
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        """Возвращает валидированные данные без создания объектов."""
        return validated_data

    def update(self, instance, validated_data):
        """Не изменяет объект и возвращает переданный экземпляр."""
        return instance


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для чтения."""
    
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True, source='ingredient_in_recipes', read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ('id',)

    def get_is_favorited(self, obj):
        """Возвращает True, если рецепт в избранном у текущего пользователя."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Возвращает True, если рецепт в корзине у текущего пользователя."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()

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

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'tags', 'image', 'name',
            'text', 'cooking_time'
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        """Валидирует ингредиенты, теги и время готовки."""
        is_update = self.instance is not None
        required_fields = (
            'ingredients', 'tags', 'name', 'text', 'cooking_time'
        )

        if is_update:
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
        seen_ing_ids = set()
        for item in ingredients:
            ing_id = item['id']
            if ing_id in seen_ing_ids:
                raise serializers.ValidationError({
                    'ingredients': ['Ингредиент не должен повторяться.']
                })
            seen_ing_ids.add(ing_id)
        existing_count = Ingredient.objects.filter(
            id__in=seen_ing_ids
        ).count()
        if existing_count != len(seen_ing_ids):
            raise serializers.ValidationError({
                'ingredients': ['Некорректные идентификаторы ингредиентов.']
            })

        if not tags:
            raise serializers.ValidationError({'tags': ['Обязательное поле.']})
        tag_ids = [t.id for t in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError({
                'tags': ['Теги не должны повторяться.']
            })

        if attrs.get('cooking_time', 0) < 1:
            raise serializers.ValidationError({
                'cooking_time': ['Значение должно быть >= 1.']
            })
        return attrs

    def _set_ingredients(self, recipe, ingredients):
        """Полностью заменяет ингредиенты рецепта указанным списком."""
        IngredientInRecipe.objects.filter(recipe=recipe).delete()
        bulk = []
        for item in ingredients:
            ingredient = Ingredient.objects.get(pk=item['id'])
            bulk.append(
                IngredientInRecipe(
                    recipe=recipe, ingredient=ingredient, amount=item['amount']
                )
            )
        IngredientInRecipe.objects.bulk_create(bulk)

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
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            self._set_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        """Возвращает представление через сериализатор чтения рецепта."""
        return RecipeReadSerializer(instance, context=self.context).data


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с его рецептами и их количеством."""
    
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        """Возвращает рецепты автора; учитывает параметр recipes_limit."""
        request = self.context.get('request')
        limit = 0
        if request:
            try:
                limit = int(request.query_params.get('recipes_limit') or 0)
            except Exception:
                limit = 0
        qs = Recipe.objects.filter(author=obj).order_by('-id')
        if limit and limit > 0:
            qs = qs[:limit]
        return RecipeMinifiedSerializer(
            qs,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов автора."""
        return Recipe.objects.filter(author=obj).count()
