from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import exceptions, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework.viewsets import ModelViewSet

from api.filters import RecipeFilter
from api.permissions import IsAuthor
from api.serializers import (
    IngredientSpecificationSerializer, RecipeAbbreviationSerializer,
    RecipeSerializer,
    TagSerializer, ChangePasswordSerializer, CreateUserSerializer,
    UserFavoriteSerializer, UserSerializer)
from api.utils import dict_to_print_data, generate_pdf
from recipes.models import IngredientSpecification, Tag, Recipe

User = get_user_model()


class IngredientSpecificationViewSet(ModelViewSet):
    queryset = IngredientSpecification.objects.all()
    serializer_class = IngredientSpecificationSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = self.request.GET.get('name', None)
        if search_term:
            starts_with_filter = Q(name__istartswith=search_term)
            contains_filter = Q(name__icontains=search_term)
            queryset = queryset.filter(starts_with_filter | contains_filter)
            queryset = sorted(queryset,
                              key=lambda x: not x.name.lower().startswith(
                                  search_term.lower()))
        return queryset


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get']
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    serializer_class = RecipeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action in ['create']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthor]
        return [permission() for permission in permission_classes]

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=RecipeAbbreviationSerializer,)
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe in request.user.favorite_recipes.all():
            raise ValidationError({"errors": "вы уже добавили рецепт"})
        recipe.is_favorited.add(request.user)
        return Response(RecipeAbbreviationSerializer(
                        recipe, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe not in request.user.favorite_recipes.all():
            raise ValidationError({"errors": "вы не добавляли рецепт"})
        recipe.is_favorited.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=RecipeAbbreviationSerializer,)
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe in request.user.shopping_cart.all():
            raise ValidationError({"errors": "вы уже добавили рецепт"})
        recipe.is_in_shopping_cart.add(request.user)
        return Response(RecipeAbbreviationSerializer(
                        recipe, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe not in request.user.shopping_cart.all():
            raise ValidationError({"errors": "вы не добавляли рецепт"})
        recipe.is_in_shopping_cart.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def download_shopping_cart(self, request):
        if not request.user.is_authenticated:
            raise exceptions.NotAuthenticated()
        grouped_ingredients = {}
        for recipe in request.user.shopping_cart.all():
            for ingredient in recipe.ingredient_set.all():
                key = ingredient.specification.id
                if key in grouped_ingredients:
                    grouped_ingredients[key]['amount'] += ingredient.amount
                else:
                    grouped_ingredients[key] = {
                        'name': ingredient.specification.name,
                        'measurement_unit':
                        ingredient.specification.measurement_unit,
                        'amount': ingredient.amount,
                    }
        return generate_pdf(dict_to_print_data(grouped_ingredients.values()))


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'delete']

    def get_permissions(self):
        if self.action in ['create', 'list']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('DELETE')

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me',)
    def get_current_user_info(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',)
    def change_password(self, request):
        serializer = ChangePasswordSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',)
    def get_subscriptions(self, request):
        queryset = request.user.following.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserFavoriteSerializer(
                page,
                many=True,
                context={'request': request},)
            return self.get_paginated_response(serializer.data)
        serializer = UserFavoriteSerializer(
            queryset,
            many=True,
            context={'request': request},)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=UserFavoriteSerializer,)
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if author in request.user.following.all():
            raise ValidationError({"errors": "вы уже подписаны"})
        if author == request.user:
            raise ValidationError({"errors": "нельзя подписаться на себя"})
        request.user.following.add(author)
        return Response(UserFavoriteSerializer(author, context={
            'request': request},).data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if author not in request.user.following.all():
            raise ValidationError({"errors": "вы не подписаны на автора"})
        request.user.following.remove(author)
        return Response(status=status.HTTP_204_NO_CONTENT)
