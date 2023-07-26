import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from api.models import Ingredient, IngredientSpecification, Recipe, Tag
from users.serializers import UserSerializer
# from users.models import User


class IngredientSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientSpecification
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    name = SerializerMethodField()
    measurement_unit = SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit', 'amount']

    def get_name(self, instance):
        return instance.specification.name

    def get_measurement_unit(self, instance):
        return instance.specification.measurement_unit


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    # is_favorited = SerializerMethodField()
    # is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
            # 'is_favorited', 'is_in_shopping_cart',
        ]

    # def get_is_favorited(self, instance):
    #     return (self.context['request'].user.favorite_recipes.filter(
    #         recipe=instance).exists())

    # def get_is_in_shopping_cart(self, instance):
    #     return (self.context['request'].user.shopping_cart.filter(
    #         recipe=instance).exists())
