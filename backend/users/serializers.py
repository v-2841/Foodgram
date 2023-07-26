from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

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
        return (self.context['request'].user.follower.filter(
            following=instance).exists())


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
