from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    TokenLoginView,
    TokenLogoutView,
    TagViewSet,
    IngredientViewSet,
    UsersViewSet,
    SetPasswordView,
    AvatarView,
    SubscriptionsView,
    SubscribeView,
    RecipeViewSet,
    DownloadShoppingCartView,
)


api_v1_router = DefaultRouter()

api_v1_router.register(r'users', UsersViewSet, basename='users')
# Register read-only endpoints
api_v1_router.register(r'tags', TagViewSet, basename='tags')
api_v1_router.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredients'
)
api_v1_router.register(r'recipes', RecipeViewSet, basename='recipes')



auth_urlpatterns = [
    path('token/login/', TokenLoginView.as_view(), name='token-login'),
    path('token/logout/', TokenLogoutView.as_view(), name='token-logout'),
]


urlpatterns = [
    path('auth/', include((auth_urlpatterns, 'auth'))),
    path('users/set_password/', SetPasswordView.as_view(), name='set-password'),
    path('users/me/avatar/', AvatarView.as_view(), name='set-avatar'),
    path('users/subscriptions/', SubscriptionsView.as_view(), name='subscriptions'),
    path('users/<int:id>/subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('recipes/download_shopping_cart/', DownloadShoppingCartView.as_view(), name='download-cart'),
    path('', include(api_v1_router.urls)),
]
