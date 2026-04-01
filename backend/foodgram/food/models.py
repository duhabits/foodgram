import random
import string

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from core.constants import (
    MAX_LENGTH_INGREDIENT_NAME,
    MAX_LENGTH_MEASUREMENT_UNIT,
    MAX_LENGTH_RECIPE_NAME,
    MAX_LENGTH_SHORT_CODE,
    MAX_LENGTH_TAG_NAME,
    MAX_LENGTH_TAG_SLUG,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
    MAX_LENGTH_ADMIN_NAME,
)
from food.services import generate_unique_short_code


User = get_user_model()


class Tag(models.Model):

    name = models.CharField(
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
        verbose_name='Название',
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:MAX_LENGTH_ADMIN_NAME]


class Ingredient(models.Model):

    name = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_NAME,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_MEASUREMENT_UNIT,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement',
            ),
        )

    def __str__(self):
        return (f'{self.name}, {self.measurement_unit}')[
            :MAX_LENGTH_ADMIN_NAME
        ]


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=MAX_LENGTH_RECIPE_NAME,
        verbose_name='Название',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    cooking_time = models.IntegerField(
        validators=(MinValueValidator(MIN_COOKING_TIME),),
        verbose_name='Время приготовления (мин)',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name[:MAX_LENGTH_ADMIN_NAME]


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    amount = models.IntegerField(
        validators=(MinValueValidator(MIN_AMOUNT),),
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        unique_together = (
            'recipe',
            'ingredient',
        )

    def __str__(self):
        return (
            f'{self.recipe.name} — {self.ingredient.name} ' f'({self.amount})'
        )


class BaseUserRecipe(models.Model):
    """Абстрактная модель для связи пользователя с рецептом"""

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
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique',
            ),
        )

    def __str__(self):
        return (
            f'{self.user.username} — {self.recipe.name} '
            f'({self._meta.verbose_name})'
        )


class Favorite(BaseUserRecipe):
    """Модель избранного"""

    class Meta(BaseUserRecipe.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(BaseUserRecipe):
    """Модель корзины покупок"""

    class Meta(BaseUserRecipe.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_link',
        verbose_name='Рецепт',
    )
    code = models.CharField(
        max_length=MAX_LENGTH_SHORT_CODE,
        unique=True,
        db_index=True,
        verbose_name='Короткий код',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.code} → {self.recipe.name}'

    @classmethod
    def generate_unique_code(cls, length=MAX_LENGTH_SHORT_CODE):
        return generate_unique_short_code(cls, length)
