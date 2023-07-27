from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientSpecificationViewSet, RecipeViewSet, TagViewSet

router = DefaultRouter()
router.register(r'ingredients', IngredientSpecificationViewSet,
                basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
urlpatterns = [
    path('', include(router.urls)),
]
