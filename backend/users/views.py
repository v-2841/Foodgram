from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework.viewsets import ModelViewSet

from users.models import User
from users.serializers import (
    ChangePasswordSerializer, CreateUserSerializer, UserFavoriteSerializer,
    UserSerializer)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'delete']

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Метод \"DELETE\" не разрешен."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me',
        )
    def get_current_user_info(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
        )
    def change_password(self, request):
        serializer = ChangePasswordSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
    )
    def get_subscriptions(self, request):
        serializer = UserFavoriteSerializer(
            request.user.following.all(),
            many=True,
            context={'request': request},
            )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=UserFavoriteSerializer,
        )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if author in request.user.following.all():
            raise ValidationError({"errors": "вы уже подписаны"})
        if author == request.user:
            raise ValidationError({"errors": "нельзя подписаться на себя"})
        request.user.following.add(author)
        return Response(UserFavoriteSerializer(author).data,
                        status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if author not in request.user.following.all():
            raise ValidationError({"errors": "вы не подписаны на автора"})
        request.user.following.remove(author)
        return Response(status=status.HTTP_204_NO_CONTENT)
