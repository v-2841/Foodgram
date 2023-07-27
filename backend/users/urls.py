from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
urlpatterns = [
    re_path(r'auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
