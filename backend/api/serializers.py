import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from api.services import build_absolute_file_url
from ingredients.models import Ingredient
from recipes.models import IngredientInRecipe, Recipe
from tags.models import Tag


User = get_user_model()


class TokenCreateSerializer(serializers.Serializer):
    """Сериализатор для получения токена авторизации (email + пароль)."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': ['Неверные учетные данные.']
            })
        if not user.check_password(password):
            raise serializers.ValidationError({
                'email': ['Неверные учетные данные.']
            })
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id',)


class UserSerializer(serializers.ModelSerializer):
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
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        from interactions.models import Subscription
        return Subscription.objects.filter(
            user=request.user,
            author=obj
        ).exists()

    def get_avatar(self, obj):
        request = self.context.get('request')
        return build_absolute_file_url(request, obj.avatar)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class SetAvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField(required=True)

    def save(self, **kwargs):
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
        return validated_data

    def update(self, instance, validated_data):
        return instance


# Сериализаторы рецептов

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
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
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id',)

    def get_image(self, obj):
        request = self.context.get('request')
        return build_absolute_file_url(request, obj.image)


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAmountWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class RecipeReadSerializer(serializers.ModelSerializer):
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
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        from interactions.models import Favorite
        return Favorite.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        from interactions.models import ShoppingCart
        return ShoppingCart.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()

    def get_image(self, obj):
        request = self.context.get('request')
        return build_absolute_file_url(request, obj.image)


class RecipeWriteSerializer(serializers.ModelSerializer):
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
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
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
        return RecipeReadSerializer(instance, context=self.context).data


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
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
        return Recipe.objects.filter(author=obj).count()
