from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint

from users.validators import validate_username


class User(AbstractUser):
    username = models.CharField(
        validators=(validate_username,),
        max_length=settings.USERPROFILE_LENGHT,
        blank=False,
        unique=True,
        verbose_name='Ник',
    )
    email = models.EmailField(
        max_length=settings.EMAIL_LENGHT,
        blank=False,
        unique=True,
        verbose_name='Электронная почта',
    )
    first_name = models.CharField(
        max_length=settings.USERPROFILE_LENGHT,
        blank=False,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=settings.USERPROFILE_LENGHT,
        blank=False,
        verbose_name='Фамилия',
    )
    following = models.ManyToManyField(
        'self',
        through='Follow',
        symmetrical=False,
        related_name='followers',
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    @property
    def recipes_counter(self):
        return self.recipes.all().count()

    recipes_counter.fget.short_description = 'Количество рецептов'

    @property
    def followers_counter(self):
        return self.followers.all().count()

    followers_counter.fget.short_description = 'Количество подписчиков'


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_set',
        verbose_name='Подписчик',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower_set',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ('follower__username',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(
                fields=['follower', 'following'], name='not_unique_follow'),
            CheckConstraint(
                check=~Q(follower=F('following')), name='self_follow'),
        ]

    def __str__(self):
        return self.follower.username + ' - ' + self.following.username
