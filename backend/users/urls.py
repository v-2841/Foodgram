from django.urls import include, path, re_path

from users.views import ChangePasswordView

urlpatterns = [
    path('users/set_password/', ChangePasswordView.as_view()),
    re_path(r'auth/', include('djoser.urls.authtoken')),
]
