# from rest_framework import status
# from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.models import IngredientSpecification, Tag, Recipe
from api.serializers import (
    IngredientSpecificationSerializer, RecipeSerializer, TagSerializer,
    )


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
    serializer_class = RecipeSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
