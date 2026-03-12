from django.contrib import admin
from django.db.models import Count
from django.core.exceptions import ValidationError
from .models import (
    Tag, Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, ShortLink
)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для ингредиентов в рецепте"""
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов"""
    list_display = ('id', 'name', 'slug')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов"""
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов"""
    list_display = (
        'id', 'name', 'author', 'cooking_time',
        'created_at', 'favorites_count', 'has_image'
    )
    list_display_links = ('id', 'name')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'cooking_time')
    readonly_fields = ('created_at', 'favorites_count')
    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('author', 'name', 'text', 'cooking_time', 'image')
        }),
        ('Связи', {
            'fields': ('tags', 'ingredients'),
            'classes': ('wide',)
        }),
        ('Даты', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Оптимизация запросов и добавление аннотации"""
        queryset = super().get_queryset(request)
        return queryset.select_related('author').prefetch_related(
            'tags', 'ingredients'
        ).annotate(
            favorites_count=Count('favorites')
        )

    def favorites_count(self, obj):
        """Количество добавлений в избранное"""
        return getattr(obj, 'favorites_count', obj.favorites.count())
    favorites_count.short_description = 'В избранном'
    favorites_count.admin_order_field = 'favorites_count'

    def has_image(self, obj):
        """Проверка наличия изображения"""
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Есть изображение'

    def save_model(self, request, obj, form, change):
        """Проверка наличия изображения при создании"""
        if not obj.image and not change:
            raise ValidationError("Рецепт должен содержать изображение")
        super().save_model(request, obj, form, change)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов рецепта"""
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_display_links = ('id', 'recipe')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient__measurement_unit',)
    raw_id_fields = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранного"""
    list_display = ('id', 'user', 'recipe', 'get_recipe_author')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'recipe__name', 'recipe__author__username')
    raw_id_fields = ('user', 'recipe')
    list_filter = ('recipe__author',)

    def get_recipe_author(self, obj):
        return obj.recipe.author.username
    get_recipe_author.short_description = 'Автор рецепта'
    get_recipe_author.admin_order_field = 'recipe__author__username'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для корзины покупок"""
    list_display = ('id', 'user', 'recipe', 'get_recipe_author')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'recipe__name', 'recipe__author__username')
    raw_id_fields = ('user', 'recipe')
    list_filter = ('recipe__author',)

    def get_recipe_author(self, obj):
        return obj.recipe.author.username
    get_recipe_author.short_description = 'Автор рецепта'
    get_recipe_author.admin_order_field = 'recipe__author__username'


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    """Админка для коротких ссылок"""
    list_display = ('id', 'code', 'recipe', 'created_at', 'get_recipe_link')
    list_display_links = ('id', 'code')
    search_fields = ('code', 'recipe__name')
    readonly_fields = ('created_at', 'code')
    raw_id_fields = ('recipe',)

    def get_recipe_link(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<a href="/s/{}/" target="_blank">Перейти</a>',
            obj.code
        )
    get_recipe_link.short_description = 'Ссылка'