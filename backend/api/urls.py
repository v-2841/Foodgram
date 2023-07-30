from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientSpecificationViewSet, RecipeViewSet,
                       TagViewSet, UserViewSet)

router = DefaultRouter()
router.register(r'ingredients', IngredientSpecificationViewSet,
                basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users', UserViewSet, basename='users')
urlpatterns = [
    path('', include(router.urls)),
    re_path(r'auth/', include('djoser.urls.authtoken')),
]
