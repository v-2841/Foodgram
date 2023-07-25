from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from users.views import ChangePasswordView, UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
urlpatterns = [
    path('users/set_password/', ChangePasswordView.as_view()),
    re_path(r'auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
