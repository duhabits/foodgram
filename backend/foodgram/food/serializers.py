import base64
import uuid
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from .models import (
    Recipe,
    Tag,
    Ingredient,
    RecipeIngredient,
    RecipeTag,
    Favorite,
    ShoppingCart,
)
from .fields import Base64ImageField
from user.serializers import UserSerializer

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте (для GET запросов)"""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Минифицированный сериализатор рецепта"""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор списка рецептов"""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_ingredients(self, obj):
        """Получаем ингредиенты через RecipeIngredient"""
        recipe_ingredients = obj.recipe_ingredients.all()
        return [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount
            }
            for ri in recipe_ingredients
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shopping_cart.filter(user=request.user).exists()
        return False


class IngredientCreateSerializer(serializers.Serializer):
    """Сериализатор для создания ингредиента в рецепте (ТОЛЬКО ДЛЯ ЗАПИСИ)"""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор создания/обновления рецепта"""

    ingredients = IngredientCreateSerializer(many=True, write_only=True)  # <-- Добавлен write_only
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True  # <-- Добавлен write_only
    )
    image = Base64ImageField(required=True, allow_null=False, write_only=True)  # <-- Добавлен write_only
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один ингредиент'
            )

        ingredient_ids = [item['id'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один тег'
            )

        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться')

        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        image = validated_data.pop('image')

        recipe = Recipe.objects.create(**validated_data)

        if image:
            recipe.image = image
            recipe.save()

        # Добавляем теги
        for tag in tags_data:
            RecipeTag.objects.create(recipe=recipe, tag=tag)

        # Добавляем ингредиенты
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'],
            )

        # Возвращаем рецепт для сериализации через RecipeListSerializer
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        image = validated_data.pop('image', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if image is not None:
            if instance.image:
                instance.image.delete(save=False)
            instance.image = image

        instance.save()

        if tags_data is not None:
            instance.tags.clear()
            for tag in tags_data:
                RecipeTag.objects.create(recipe=instance, tag=tag)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount'],
                )

        return instance