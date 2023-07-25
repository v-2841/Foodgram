from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from users.models import User


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate_password(self, value):
        validate_password(value)
        return value


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'id', 'is_subscribed')
