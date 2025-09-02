from django.db.models import Sum
from django.http import HttpResponse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import generics, mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse

from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    TokenCreateSerializer,
    TagSerializer,
    IngredientSerializer,
    UserSerializer,
    UserCreateSerializer,
    SetPasswordSerializer,
    SetAvatarSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeMinifiedSerializer,
    UserWithRecipesSerializer,
)
from api.filters import RecipeFilter, NameSearchFilter
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag
)
from users.models import User


class TokenLoginView(generics.GenericAPIView):
    """Получение токена авторизации по email и паролю."""

    serializer_class = TokenCreateSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        """Возвращает auth_token для валидных учетных данных."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


class TokenLogoutView(generics.GenericAPIView):
    """Удаление токена текущего пользователя."""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """Удаляет все токены текущего пользователя и возвращает 204."""
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Просмотр тегов (список и детальная информация)."""

    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Поиск и просмотр ингредиентов (список и детально)."""

    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = Ingredient.objects.all().order_by('id')
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)


class UsersViewSet(viewsets.ModelViewSet):
    """Работа с пользователями и их профилем/подписками."""

    queryset = User.objects.all().order_by('id')
    http_method_names = ('get', 'post', 'put', 'delete')

    def get_permissions(self):
        """Определяет права доступа в зависимости от действия."""
        if self.action in ('list', 'retrieve', 'create'):
            return (AllowAny(),)
        if self.action == 'me':
            return (IsAuthenticated(),)
        return (IsAuthenticated(),)

    def get_serializer_class(self):
        """Возвращает сериализатор для текущего действия."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        """Запрещает полный update пользователей (405)."""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        """Запрещает частичный update пользователей (405)."""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        """Запрещает удаление пользователей (405)."""
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        """Возвращает данные профиля текущего пользователя."""
        serializer = UserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='set_password',
    )
    def set_password(self, request):
        """Меняет пароль при верном текущем пароле, возвращает 204."""
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current = serializer.validated_data['current_password']
        new = serializer.validated_data['new_password']
        if not request.user.check_password(current):
            return Response(
                {'current_password': ['Неверный пароль.']},
                status=400,
            )
        try:
            validate_password(new, user=request.user)
        except DjangoValidationError as e:
            return Response({'new_password': list(e.messages)}, status=400)
        request.user.set_password(new)
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('put',),
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def avatar(self, request):
        """Устанавливает аватар текущего пользователя из base64."""
        serializer = SetAvatarSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        url = user.avatar.url
        if request:
            url = request.build_absolute_uri(url)
        return Response({'avatar': url})

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар текущего пользователя, если он установлен."""
        if request.user.avatar:
            request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        qs = User.objects.filter(subscribers__user=request.user).distinct()
        page = self.paginate_queryset(qs)
        serializer = UserWithRecipesSerializer(
            page or qs,
            many=True,
            context={'request': request},
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request, pk=None):
        """Оформляет подписку на автора, если это не сам пользователь."""
        author = self.get_object()
        if author == request.user:
            return Response(
                {'detail': 'Нельзя подписаться на себя.'},
                status=400,
            )
        _, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if not created:
            return Response(
                {'detail': 'Подписка уже существует.'},
                status=400,
            )
        serializer = UserWithRecipesSerializer(
            author,
            context={'request': request},
        )
        return Response(serializer.data, status=201)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        """Отписывает от автора, если подписка существовала."""
        author = self.get_object()
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Не была оформлена подписка.'},
                status=400,
            )
        return Response(status=204)


class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD для рецептов и дополнительные действия (лайки, корзина)."""

    permission_classes = (IsAuthorOrReadOnly,)
    queryset = (
        Recipe.objects.all()
        .select_related('author')
        .prefetch_related('tags', 'ingredient_in_recipes__ingredient')
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбирает сериализатор: чтение для list/retrieve, иначе запись."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """Сохраняет рецепт, автора берет из сериализатора."""
        serializer.save()

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное пользователя."""
        recipe = self.get_object()
        _, created = Favorite.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            return Response({'detail': 'Уже в избранном.'}, status=400)
        return Response(
            RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            ).data,
            status=201
        )

    @favorite.mapping.delete
    def unfavorite(self, request, pk=None):
        """Удаляет рецепт из избранного пользователя."""
        recipe = self.get_object()
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response({'detail': 'Не было в избранном.'}, status=400)
        return Response(status=204)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def add_to_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок пользователя."""
        recipe = self.get_object()
        _, created = ShoppingCart.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            return Response({'detail': 'Уже в списке покупок.'}, status=400)
        return Response(
            RecipeMinifiedSerializer(
                recipe,
                context={'request': request}
            ).data,
            status=201
        )

    @add_to_cart.mapping.delete
    def remove_from_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок пользователя."""
        recipe = self.get_object()
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Не было в списке покупок.'},
                status=400,
            )
        return Response(status=204)

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(AllowAny,),
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_path = reverse(
            'recipe-short-link',
            kwargs={'short_id': recipe.id},
        )
        absolute_url = (
            request.build_absolute_uri(short_path)
            if request else short_path
        )
        return Response({'short-link': absolute_url})

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Формирует и отдает txt-файл со списком покупок пользователя."""
        ingredients = (
            IngredientInRecipe.objects
            .filter(recipe__in_carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        lines = []
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            lines.append(f"{name} ({unit}) — {amount}")
        content = "\n".join(lines) or "Список покупок пуст."
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response
