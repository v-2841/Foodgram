from django_filters import rest_framework as filters

from api.models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(
        field_name='tags__slug',
        lookup_expr='icontains',
    )
    author = filters.NumberFilter(
        field_name='author__id',
    )
    is_favorited = filters.BooleanFilter()
    is_in_shopping_cart = filters.BooleanFilter()

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')
