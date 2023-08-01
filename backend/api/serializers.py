# type: ignore
import base64
import binascii
from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.db.models import F
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from recipes.models import Ingredient, IngredientSpecification, Recipe, Tag

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = SerializerMethodField(method_name='is_subscribed_by_user')

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'id', 'is_subscribed')

    def is_subscribed_by_user(self, instance):
        try:
            return (self.context['request'].user.following.filter(
                username=instance).exists())
        except Exception:
            return False


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
            max_image_size = 2 * 1024 * 1024
            if len(imgstr) * 3 / 4 > max_image_size:  # About 2 Mb
                raise serializers.ValidationError(
                    "Image size exceeds the maximum allowed size.")
            try:
                decoded_image = self.decode_base64_image(imgstr)
            except (TypeError, binascii.Error):
                raise serializers.ValidationError("Invalid base64 format")
            image_name = "image.{0}".format(ext)
            data = ContentFile(decoded_image, name=image_name)
        return super().to_internal_value(data)

    def decode_base64_image(self, imgstr):
        with ThreadPoolExecutor() as executor:
            decoded_image = executor.submit(base64.b64decode, imgstr)
        return decoded_image.result()


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None)
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart',
        ]

    def get_ingredients(self, instance):
        ingredients = instance.ingredients.values(
            "id", "name", "measurement_unit", amount=F("ingredient__amount")
        )
        return ingredients

    def get_is_favorited(self, instance):
        try:
            return (self.context['request'].user.favorite_recipes.filter(
                id=instance.id).exists())
        except Exception:
            return False

    def get_is_in_shopping_cart(self, instance):
        try:
            return (self.context['request'].user.shopping_cart.filter(
                id=instance.id).exists())
        except Exception:
            return False

    def validate(self, data):
        try:
            tags = self.initial_data['tags']
        except KeyError:
            raise serializers.ValidationError(
                    'Отсутствует поле tags')
        try:
            ingredients = self.initial_data['ingredients']
        except KeyError:
            raise serializers.ValidationError(
                    'Отсутствует поле ingredients')
        for tag in tags:
            if not Tag.objects.filter(id=tag).exists():
                raise serializers.ValidationError(
                    'Указанного тега не существует')
        for ingredient in ingredients:
            if not IngredientSpecification.objects.filter(
                    id=ingredient['id']).exists():
                raise serializers.ValidationError(
                    'Указанного ингредиента не существует')
        data.update(
            {
                "tags": Tag.objects.filter(pk__in=tags),
                "ingredients": ingredients,
            }
        )
        return data

    def create_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            Ingredient.objects.create(
                recipe=recipe,
                specification=IngredientSpecification.objects.get(
                    pk=ingredient['id']),
                amount=ingredient['amount'],
            )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)


class RecipeAbbreviationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class ChangePasswordSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('new_password', 'current_password')

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {"current_password": "Неверный пароль."})
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'id', 'password')

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserFavoriteSerializer(serializers.ModelSerializer):
    is_subscribed = SerializerMethodField(method_name='is_subscribed_by_user')
    recipes = RecipeAbbreviationSerializer(many=True)
    recipes_count = SerializerMethodField(method_name='user_recipes_count')

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        ]

    def is_subscribed_by_user(self, instance):
        try:
            return (self.context['request'].user.following.filter(
                username=instance).exists())
        except Exception:
            return False

    def user_recipes_count(self, instance):
        return instance.recipes.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        recipes_limit = self.context[
            'request'].query_params.get('recipes_limit', None)
        if (recipes_limit is not None
                and len(data['recipes']) > int(recipes_limit)):
            data['recipes'] = data['recipes'][:int(recipes_limit)]
        return data
