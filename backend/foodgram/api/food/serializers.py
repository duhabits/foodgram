from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from rest_framework import serializers

from api.food.fields import Base64ImageField
from api.user.serializers import UserSerializer
from food.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
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


class IngredientCreateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), write_only=True
    )
    image = Base64ImageField(required=True, allow_null=False, write_only=True)
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

    def validate_ingredients(self, ingredients_data):
        if not ingredients_data:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один ингредиент'
            )

        ingredient_ids = [
            ingredient['id'].id for ingredient in ingredients_data
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )

        return ingredients_data

    def validate_tags(self, tags_data):
        if not tags_data:
            raise serializers.ValidationError(
                'Нужно добавить хотя бы один тег'
            )

        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError('Теги не должны повторяться')

        return tags_data

    @staticmethod
    def create_recipe_ingredients(recipe, ingredients_data):
        """Статический метод для массового создания ингредиентов рецепта"""
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'],
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        image = validated_data.pop('image')

        recipe = Recipe.objects.create(image=image, **validated_data)

        recipe.tags.set(tags_data)
        self.create_recipe_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        image = validated_data.pop('image', None)

        instance = super().update(instance, validated_data)

        if image:
            if instance.image:
                instance.image.delete(save=False)
            instance.image = image

        instance.save()

        if tags_data:
            instance.tags.set(tags_data)

        if ingredients_data:
            instance.recipe_ingredients.all().delete()
            self.create_recipe_ingredients(instance, ingredients_data)

        return instance
