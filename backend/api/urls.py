from django.urls import include, path

from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    TokenLoginView,
    TokenLogoutView,
    UsersViewSet,
)


api_v1_router = DefaultRouter()

api_v1_router.register(
    r'users',
    UsersViewSet,
    basename='users'
)
api_v1_router.register(
    r'tags',
    TagViewSet,
    basename='tags'
)
api_v1_router.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredients'
)
api_v1_router.register(
    r'recipes',
    RecipeViewSet,
    basename='recipes'
)

auth_urlpatterns = [
    path('token/login/', TokenLoginView.as_view(), name='token-login'),
    path('token/logout/', TokenLogoutView.as_view(), name='token-logout'),
]

urlpatterns = [
    path('auth/', include((auth_urlpatterns, 'auth'))),
    path('', include(api_v1_router.urls)),
]
