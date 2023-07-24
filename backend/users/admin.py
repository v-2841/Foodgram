from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import User, Follow


class FollowAdmin(admin.ModelAdmin):
    search_fields = ['follower__username', 'following__username']


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.unregister(Group)
