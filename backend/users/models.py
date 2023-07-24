from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_username

USER = 'user'
ADMIN = 'admin'
MODERATOR = 'moderator'

ROLE_CHOICES = [
    (USER, USER),
    (ADMIN, ADMIN),
    (MODERATOR, MODERATOR),
]


class User(AbstractUser):
    username = models.CharField(
        validators=(validate_username,),
        max_length=64,
        unique=True,
        verbose_name='Ник',
    )
    email = models.EmailField(
        max_length=256,
        unique=True,
        verbose_name='Электронная почта',
    )
    role = models.CharField(
        max_length=16,
        choices=ROLE_CHOICES,
        default=USER,
        blank=True,
        verbose_name='Роль',
    )
    first_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Фамилия',
    )
    confirmation_code = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name='Код подтверждения',
    )

    @property
    def is_user(self):
        return self.role == USER

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_staff

    @property
    def is_moderator(self):
        return self.role == MODERATOR

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'], name='not_unique_follow'),
        ]

    def __str__(self):
        return self.follower.username + ' - ' + self.following.username
