from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class NameSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, _name, value):
        user = self.request.user if self.request else None
        if value and user and user.is_authenticated:
            return queryset.filter(in_favorites__user=user)
        return queryset

    def filter_is_in_cart(self, queryset, _name, value):
        user = self.request.user if self.request else None
        if value and user and user.is_authenticated:
            return queryset.filter(in_carts__user=user)
        return queryset
