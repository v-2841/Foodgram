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

    class Meta:
        ordering = ('id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class IngredientSpecification(models.Model):
    name = models.CharField(max_length=64)
    measurement_unit = models.CharField(max_length=16)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Свойства ингредиента'
        verbose_name_plural = 'Свойства ингредиентов'

    def __str__(self):
        return self.name + ', ' + self.measurement_unit


class Ingredient(models.Model):
    specification = models.ForeignKey(
        IngredientSpecification,
        on_delete=models.CASCADE,
    )
    amount = models.SmallIntegerField(
        validators=[
            MaxValueValidator(10000),
            MinValueValidator(0),
        ],
        error_messages={
            'validators': 'Введите число от 0 до 10000'
        },
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return (self.specification.name + ' - ' + str(self.amount)
                + ' ' + self.specification.measurement_unit)


class Recipe(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='Название',
    )
    text = models.TextField(
        max_length=1024,
        verbose_name='Описание'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    cooking_time = models.SmallIntegerField(
        verbose_name='Время приготовления',
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
        blank=True,
        null=True,
        default=None,
        verbose_name='Изображение',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
    )
    is_favorited = models.ManyToManyField(
        User,
        through='UserFavoritedRecipe',
        related_name='favorited_recipes',
    )
    is_in_shopping_cart = models.ManyToManyField(
        User,
        through='UserShoppingCart',
        related_name='shopping_cart'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


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
        ordering = ('id',)
        verbose_name = 'Теги рецепта'
        verbose_name_plural = 'Теги рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'], name='not_unique_tag'),
        ]

    def __str__(self):
        return self.recipe.name + ' #' + self.tag.name


class UserFavoritedRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Любимый рецепт'
        verbose_name_plural = 'Любимые рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='already_favorited_recipe'),
        ]

    def __str__(self):
        return self.user.username + ' - ' + self.recipe.name


class UserShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='already_in_shopping_cart'),
        ]

    def __str__(self):
        return self.user.username + ' - ' + self.recipe.name
