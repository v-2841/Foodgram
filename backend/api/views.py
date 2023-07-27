from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import RecipeFilter
from api.models import IngredientSpecification, Tag, Recipe
from api.permissions import IsAuthor
from api.serializers import (
    IngredientSpecificationSerializer, RecipeAbbreviationSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, ShoppingCartSerializer,
    TagSerializer,
    )
from api.utils import generate_pdf


class IngredientSpecificationViewSet(ModelViewSet):
    queryset = IngredientSpecification.objects.all()
    serializer_class = IngredientSpecificationSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get']


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get']


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        elif self.action in ['create']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthor]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        else:
            return RecipeWriteSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=RecipeAbbreviationSerializer,
        )
    def favorite(self, request, pk=None):
        recipe = Recipe.objects.get(pk=pk)
        recipe.is_favorited.add(request.user)
        return Response(RecipeAbbreviationSerializer(recipe).data,
                        status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        Recipe.objects.get(pk=pk).is_favorited.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=RecipeAbbreviationSerializer,
        )
    def shopping_cart(self, request, pk=None):
        recipe = Recipe.objects.get(pk=pk)
        recipe.is_in_shopping_cart.add(request.user)
        return Response(RecipeAbbreviationSerializer(recipe).data,
                        status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        Recipe.objects.get(pk=pk).is_in_shopping_cart.remove(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        queryset = request.user.shopping_cart
        serializer = ShoppingCartSerializer(queryset, many=True)
        data_dict = {'data': serializer.data}
        pdf_response = generate_pdf(data_dict)
        return pdf_response
