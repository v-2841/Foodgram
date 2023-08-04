from django.contrib.auth.password_validation import validate_password
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from recipes.models import Ingredient, IngredientSpecification, Recipe, Tag
from users.models import User


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


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=IngredientSpecification.objects.all(),
    )
    name = serializers.ReadOnlyField(source='specification.name')
    measurement_unit = serializers.ReadOnlyField(
        source='specification.measurement_unit')
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializerPost(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    image = Base64ImageField(max_length=None)
    ingredients = IngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ['ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time', 'author']

    def validate_name(self, name):
        if not any(c.isalpha() for c in name):
            raise serializers.ValidationError(
                "Название должно содержать буквы")

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Вы не указали ни одного тега')
        tags_ids = self.initial_data['tags']
        if sorted(list(set(tags_ids))) != sorted(tags_ids):
            raise serializers.ValidationError(
                'Вы указали одинаковые теги')
        return tags

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Вы не указали ни одного ингредиента')
        ingredients_data = self.initial_data['ingredients']
        ingredients_ids = []
        for ingredient in ingredients_data:
            ingredients_ids.append(ingredient['id'])
        if sorted(list(set(ingredients_ids))) != sorted(ingredients_ids):
            raise serializers.ValidationError(
                'Вы указали одинаковые ингредиенты')
        return ingredients

    def validate(self, data):
        if 'tags' not in self.initial_data:
            raise serializers.ValidationError('Отсутствует поле tags')
        if 'ingredients' not in self.initial_data:
            raise serializers.ValidationError('Отсутствует поле ingredients')
        return data

    def create_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            Ingredient.objects.create(
                recipe=recipe,
                specification=ingredient['id'],
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

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context['request']}).data


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
