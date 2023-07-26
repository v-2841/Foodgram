from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientSpecificationViewSet, RecipeViewSet, TagViewSet

router = DefaultRouter()
router.register('ingredients', IngredientSpecificationViewSet,
                basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
urlpatterns = [
    path('', include(router.urls)),
]
