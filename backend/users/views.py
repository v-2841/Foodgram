from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.serializers import ChangePasswordSerializer


class ChangePasswordView(CreateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(
                    serializer.data.get("old_password")):
                return Response(
                    {"old_password": "Неверный пароль."},
                    status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.data.get("password"))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
