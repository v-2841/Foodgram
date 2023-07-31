from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        verbose_name='Название',
        db_index=True,
    )
    color = models.CharField(
        max_length=16,
        verbose_name='Цвет',
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        db_index=True,
        verbose_name='Слаг',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class IngredientSpecification(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='Название',
        db_index=True,
    )
    measurement_unit = models.CharField(
        max_length=16,
        verbose_name='Размерность',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Свойства ингредиента'
        verbose_name_plural = 'Свойства ингредиентов'

    def __str__(self):
        return self.name + ', ' + self.measurement_unit


class Recipe(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        db_index=True,
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
            MinValueValidator(1),
        ],
        error_messages={
            'validators': 'Введите число от 1 до 300'
        },
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        blank=True,
        null=True,
        default=None,
        verbose_name='Изображение',
    )
    ingredients = models.ManyToManyField(
        IngredientSpecification,
        through='Ingredient',
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
    )
    is_favorited = models.ManyToManyField(
        User,
        through='UserFavoritedRecipe',
        related_name='favorite_recipes',
    )
    is_in_shopping_cart = models.ManyToManyField(
        User,
        through='UserShoppingCart',
        related_name='shopping_cart'
    )

    @property
    def favorites_counter(self):
        return self.is_favorited.all().count()

    favorites_counter.fget.short_description = 'В избранных'

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    specification = models.ForeignKey(
        IngredientSpecification,
        on_delete=models.CASCADE,
        verbose_name='Характеристики ингредиента',
    )
    amount = models.SmallIntegerField(
        validators=[
            MaxValueValidator(10000),
            MinValueValidator(0),
        ],
        error_messages={
            'validators': 'Введите число от 0 до 10000'
        },
        verbose_name='Количество',
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return (self.specification.name + ' - ' + str(self.amount)
                + ' ' + self.specification.measurement_unit)


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ('-id',)
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
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ('-id',)
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
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='already_in_shopping_cart'),
        ]

    def __str__(self):
        return self.user.username + ' - ' + self.recipe.name
