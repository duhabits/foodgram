from django.contrib import admin
from django.db.models import Count
from .models import (
    Tag, Ingredient, Recipe, RecipeTag, 
    RecipeIngredient, Favorite, ShoppingCart, 
    Subscription, ShortLink
)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для ингредиентов в рецепте"""
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


class RecipeTagInline(admin.TabularInline):
    """Инлайн для тегов в рецепте"""
    model = RecipeTag
    extra = 1
    min_num = 1
    verbose_name = 'Тег'
    verbose_name_plural = 'Теги'


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
    list_display = ('id', 'name', 'author', 'cooking_time', 'created_at', 'favorites_count')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'cooking_time')
    readonly_fields = ('created_at', 'favorites_count')
    inlines = [RecipeIngredientInline, RecipeTagInline]
    
    def get_queryset(self, request):
        """Оптимизация запросов и добавление аннотации"""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            favorites_count=Count('favorites')
        )
    
    def favorites_count(self, obj):
        """Количество добавлений в избранное"""
        return getattr(obj, 'favorites_count', obj.favorites.count())
    favorites_count.short_description = 'В избранном'
    favorites_count.admin_order_field = 'favorites_count'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов рецепта"""
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_display_links = ('id', 'recipe')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient__measurement_unit',)


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    """Админка для тегов рецепта"""
    list_display = ('id', 'recipe', 'tag')
    list_display_links = ('id', 'recipe')
    search_fields = ('recipe__name', 'tag__name')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранного"""
    list_display = ('id', 'user', 'recipe', 'get_recipe_author')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'recipe__name', 'recipe__author__username')
    
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
    
    def get_recipe_author(self, obj):
        return obj.recipe.author.username
    get_recipe_author.short_description = 'Автор рецепта'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для подписок"""
    list_display = ('id', 'user', 'author')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'author__username')
    
    def get_queryset(self, request):
        """Запрещаем подписку на самого себя"""
        return super().get_queryset(request).exclude(user=models.F('author'))


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    """Админка для коротких ссылок"""
    list_display = ('id', 'code', 'recipe', 'created_at')
    list_display_links = ('id', 'code')
    search_fields = ('code', 'recipe__name')
    readonly_fields = ('created_at',)