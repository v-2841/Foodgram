from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=32)
    color = models.CharField(max_length=16)
    slug = models.SlugField(
        max_length=32,
        unique=True,
        db_index=True,
    )


class Ingredient(models.Model):
    name = models.CharField(max_length=32)
    amount = models.SmallIntegerField(
        validators=[
            MaxValueValidator(10000),
            MinValueValidator(0),
        ],
        error_messages={
            'validators': 'Введите число от 0 до 10000'
        },
    )
    measurement_unit = models.CharField(max_length=16)


class Recipe(models.Model):
    name = models.CharField(max_length=64)
    text = models.TextField(max_length=1024)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    cooking_time = models.SmallIntegerField(
        validators=[
            MaxValueValidator(300),
            MinValueValidator(0),
        ],
        error_messages={
            'validators': 'Введите число от 0 до 300'
        },
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None,
    )
    # ingredients = models.ManyToManyField
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
    )
    is_favorited = models.BooleanField(
        default=False,
    )
    is_in_shopping_cart = models.BooleanField(
        default=False,
    )


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'], name='not_unique_tag'),
        ]
