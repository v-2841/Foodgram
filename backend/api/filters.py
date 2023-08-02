from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(
        field_name='tags__slug',
        lookup_expr='icontains',
    )
    is_favorited = filters.BooleanFilter(method='filter_by_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_by_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def filter_by_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated and value:
            return queryset.none()
        if value and user.is_authenticated:
            return queryset.filter(is_favorited=user)
        return queryset

    def filter_by_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated and value:
            return queryset.none()
        if value and user.is_authenticated:
            return queryset.filter(is_in_shopping_cart=user)
        return queryset
