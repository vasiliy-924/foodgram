from http import HTTPStatus

from django.db import IntegrityError
from django.db.models import (
    BooleanField,
    Exists,
    OuterRef,
    Sum,
    Value,
    Count,
    F,
)
from django.http import FileResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.permissions import IsAuthorOrReadOnly
from api.pagination import LimitPageNumberPagination
from api.serializers import (
    FavoriteCreateSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    SetAvatarSerializer,
    ShoppingCartCreateSerializer,
    SubscriptionCreateSerializer,
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from api.filters import NameSearchFilter, RecipeFilter
from api.services import build_absolute_file_url, format_shopping_list
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import Subscription, User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр тегов (список и детальная информация)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Поиск и просмотр ингредиентов (список и детально)."""

    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = Ingredient.objects.all()
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)


class UsersViewSet(DjoserUserViewSet):
    """Работа с пользователями и их профилем/подписками."""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        """Аннотирует количество рецептов пользователя в recipes_count."""
        base_qs = super().get_queryset()
        return base_qs.annotate(recipes_count=Count('recipes'))

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
        serializer.save()
        return Response(
            {'avatar': build_absolute_file_url(request, request.user.avatar)}
        )

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар текущего пользователя, если он установлен."""
        request.user.avatar.delete(save=True)
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        qs = (
            User.objects
            .filter(author_subscriptions__user=request.user)
            .annotate(recipes_count=Count('recipes'))
        )
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
    def subscribe(self, request, id=None):
        """Оформляет подписку на автора через валидирующий сериализатор."""
        author = self.get_object()
        serializer = SubscriptionCreateSerializer(
            data={'author': author.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IntegrityError:
            return Response(
                {'detail': 'Подписка уже существует или недопустима.'},
                status=HTTPStatus.BAD_REQUEST,
            )
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отписывает от автора, если подписка существовала."""
        author = self.get_object()
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        return Response(
            status=(
                HTTPStatus.NO_CONTENT if deleted else HTTPStatus.BAD_REQUEST
            ),
            data=None if deleted else {
                'detail': 'Не была оформлена подписка.'
            },
        )


class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD для рецептов и дополнительные действия (лайки, корзина)."""

    permission_classes = (IsAuthorOrReadOnly,)
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбирает сериализатор: чтение для list/retrieve, иначе запись."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        """Возвращает queryset с нужными префетчами и аннотациями флагов."""
        base_qs = (
            super()
            .get_queryset()
            .select_related('author')
            .prefetch_related('tags', 'ingredient_in_recipes__ingredient')
        )

        request = getattr(self, 'request', None)
        user = getattr(request, 'user', None)

        if user and user.is_authenticated:
            favorite_exists = Favorite.objects.filter(
                user=user,
                recipe=OuterRef('pk'),
            )
            cart_exists = ShoppingCart.objects.filter(
                user=user,
                recipe=OuterRef('pk'),
            )
            return base_qs.annotate(
                is_favorited=Exists(favorite_exists),
                is_in_shopping_cart=Exists(cart_exists),
            )

        return base_qs.annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField()),
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, _request, pk=None):
        return self._create_relation(FavoriteCreateSerializer, pk)

    @favorite.mapping.delete
    def unfavorite(self, request, pk=None):
        """Удаляет рецепт из избранного пользователя."""
        self.get_object()
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe_id=pk,
        ).delete()
        return Response(
            status=(
                HTTPStatus.NO_CONTENT if deleted else HTTPStatus.BAD_REQUEST
            ),
            data=None if deleted else {'detail': 'Не было в избранном.'},
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def add_to_cart(self, _request, pk=None):
        return self._create_relation(ShoppingCartCreateSerializer, pk)

    @add_to_cart.mapping.delete
    def remove_from_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок пользователя."""
        self.get_object()
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe_id=pk,
        ).delete()
        return Response(
            status=(
                HTTPStatus.NO_CONTENT if deleted else HTTPStatus.BAD_REQUEST
            ),
            data=None if deleted else {'detail': 'Не было в списке покупок.'},
        )

    def _create_relation(self, serializer_class, pk):
        """Общий метод создания связи (избранное/список покупок)."""
        self.get_object()
        data = {
            'user': getattr(self.request.user, 'id', None),
            'recipe': pk,
        }
        serializer = serializer_class(
            data=data,
            context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(AllowAny,),
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_path = f"/s/{recipe.id}/"
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
            .filter(recipe__shoppingcart__user=request.user)
            .values(
                name=F('ingredient__name'),
                measurement_unit=F('ingredient__measurement_unit')
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('name')
        )
        file_obj = format_shopping_list(ingredients)
        response = FileResponse(
            file_obj,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response
