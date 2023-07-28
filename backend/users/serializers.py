from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from api.models import Recipe
from users.models import User


class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('password', 'old_password')

    def validate_password(self, value):
        validate_password(value)
        return value

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data['old_password']):
            raise serializers.ValidationError(
                {"old_password": "Неверный пароль."})
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = SerializerMethodField(method_name='is_subscribed_by_user')

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'id', 'is_subscribed')

    def is_subscribed_by_user(self, instance):
        try:
            return (self.context['request'].user.follower.filter(
                following=instance).exists())
        except Exception:
            return False


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


class RecipeAbbreviationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


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
            return (self.context['request'].user.follower.filter(
                following=instance).exists())
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
