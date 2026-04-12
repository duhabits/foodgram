from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count

from food.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShortLink,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр для группировки рецептов по времени приготовления"""

    title = 'Время приготовления'
    parameter_name = 'cooking_time_range'

    def lookups(self, request, model_admin):
        return (
            ('fast', 'Быстрые (до 30 мин)'),
            ('medium', 'Средние (30-60 мин)'),
            ('long', 'Долгие (более 60 мин)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return queryset.filter(cooking_time__lte=30)
        if self.value() == 'medium':
            return queryset.filter(cooking_time__gte=30, cooking_time__lte=60)
        if self.value() == 'long':
            return queryset.filter(cooking_time__gte=60)
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'created_at',
        'favorites_count',
        'get_tags_display',
        'get_ingredients_display',
        'image_preview',
    )
    list_display_links = ('id', 'name')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'cooking_time', CookingTimeFilter)
    readonly_fields = ('created_at', 'favorites_count', 'image_preview')
    filter_horizontal = ('tags',)
    inlines = [RecipeIngredientInline]

    fieldsets = (
        (
            'Основная информация',
            {
                'fields': (
                    'author',
                    'name',
                    'text',
                    'cooking_time',
                    'image_preview',
                    'image',
                )
            },
        ),
        ('Связи', {'fields': ('tags',), 'classes': ('wide',)}),
        ('Даты', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return (
            queryset.select_related('author')
            .prefetch_related('tags', 'recipe_ingredients__ingredient')
            .annotate(favorites_count=Count('favorited_by'))
        )

    @admin.display(description='В избранном', ordering='favorites_count')
    def favorites_count(self, obj):
        return getattr(obj, 'favorites_count', obj.favorited_by.count())

    @admin.display(description='Теги')
    def get_tags_display(self, obj):
        tags = obj.tags.values_list('name', flat=True)
        return ', '.join(tags) if tags else '-'

    @admin.display(description='Ингредиенты')
    def get_ingredients_display(self, obj):
        ingredients = obj.recipe_ingredients.select_related(
            'ingredient'
        ).values_list('ingredient__name', flat=True)
        result = ', '.join(list(ingredients[:5]))
        if len(ingredients) > 5:
            result += '...'
        return result if result else '-'

    @admin.display(description='Изображение')
    def image_preview(self, obj):
        return mark_safe(
            '<img src="{}" width="80" height="60" '
            'style="object-fit: cover;" />'.format(obj.image.url)
        )


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_display_links = ('id', 'recipe')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient__measurement_unit',)
    raw_id_fields = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'get_recipe_author')
    list_display_links = ('id', 'user')
    search_fields = (
        'user__username',
        'recipe__name',
        'recipe__author__username',
    )
    list_filter = ('recipe__author',)

    @admin.display(
        description='Автор рецепта', ordering='recipe__author__username'
    )
    def get_recipe_author(self, obj):
        return obj.recipe.author.username


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'get_recipe_author')
    list_display_links = ('id', 'user')
    search_fields = (
        'user__username',
        'recipe__name',
        'recipe__author__username',
    )
    list_filter = ('recipe__author',)

    @admin.display(
        description='Автор рецепта', ordering='recipe__author__username'
    )
    def get_recipe_author(self, obj):
        return obj.recipe.author.username


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'recipe',
        'created_at',
        'get_recipe_link',
    )
    list_display_links = ('id', 'code')
    search_fields = ('code', 'recipe__name')
    readonly_fields = ('created_at', 'code')
    raw_id_fields = ('recipe',)

    @admin.display(description='Ссылка')
    def get_recipe_link(self, obj):
        return format_html(
            '<a href="/s/{}/" target="_blank">Перейти</a>', obj.code
        )
