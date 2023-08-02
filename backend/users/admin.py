from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from users.models import Follow, User


class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + (
        'followers_counter', 'recipes_counter')


class FollowAdmin(admin.ModelAdmin):
    search_fields = ['follower__username', 'following__username']


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.unregister(Group)
