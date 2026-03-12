from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
import random
import string

User = get_user_model()


class Tag(models.Model):
    """Модель тегов"""
    name = models.CharField(
        max_length=200, unique=True, verbose_name='Название'
    )
    slug = models.SlugField(max_length=200, unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(max_length=200, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=50, verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement',
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецептов"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(max_length=200, verbose_name='Название')
    tags = models.ManyToManyField(
        Tag, related_name='recipes', verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', verbose_name='Ингредиенты'
    )
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления (мин)',
    )
    text = models.TextField(max_length=7000, verbose_name='Описание')
    image = models.ImageField(
        upload_to='recipes/', verbose_name='Изображение', blank=True, null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def clean(self):
        if not self.image:
            from django.core.exceptions import ValidationError
            raise ValidationError('Рецепт должен содержать изображение')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'


class RecipeIngredient(models.Model):
    """Связка рецепта и ингредиента"""
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='recipe_ingredients'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients'
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'


class Favorite(models.Model):
    """Избранное"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favorite'
            )
        ]


class ShoppingCart(models.Model):
    """Корзина покупок"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_cart'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]


class Subscription(models.Model):
    """Подписки на авторов"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribers'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            )
        ]


# ===== КОРОТКИЕ ССЫЛКИ (ДОБАВЛЕНО ПОСЛЕ ОПРЕДЕЛЕНИЯ RECIPE) =====

class ShortLink(models.Model):
    """Модель для коротких ссылок"""

    recipe = models.OneToOneField(
        Recipe,  # Теперь Recipe уже определён выше
        on_delete=models.CASCADE,
        related_name='short_link',
        verbose_name='Рецепт'
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        verbose_name='Короткий код'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} -> {self.recipe.name}'

    @classmethod
    def generate_unique_code(cls, length=6):
        """Генерация уникального кода"""
        chars = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(chars, k=length))
            if not cls.objects.filter(code=code).exists():
                return code
