from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from food.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from food.models import Favorite, ShoppingCart
from core.constants import MIN_AMOUNT
from api.common.serializers import RecipeMinifiedSerializer
from api.user.serializers import UserSerializer

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


class IngredientCreateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), write_only=True
    )
    image = Base64ImageField(required=True, allow_null=False, write_only=True)
    cooking_time = serializers.IntegerField(min_value=MIN_AMOUNT)

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

        if image:
            self.validate_image(instance, image)

        if tags_data:
            instance.tags.set(tags_data)

        if ingredients_data:
            instance.recipe_ingredients.all().delete()
            self.create_recipe_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Изображение обязательно')
        return value


class BaseFavoriteCartSerializer(serializers.ModelSerializer):

    def validate(self, data):
        request = self.context.get('request')

        if request and request.method == 'POST':
            model_class = self.Meta.model

            if model_class.objects.filter(
                user=data['user'], recipe=data['recipe']
            ).exists():
                model_verbose_name = model_class._meta.verbose_name
                raise serializers.ValidationError(
                    {'errors': f'{model_verbose_name} уже добавлен(а)'}
                )

        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe, context=self.context
        ).data


class FavoriteSerializer(BaseFavoriteCartSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(BaseFavoriteCartSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
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

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None
