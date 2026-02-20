from rest_framework import serializers
from .models import Ingredient, Tags, Food, TagsFood, IngredientFood
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'image',
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ('id', 'tag', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class FoodSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Food
        fields = (
            'id',
            'author',
            'name',
            'tags',
            'make_time',
            'description',
            'image',
        )


class FoodCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tags.objects.all()
    )

    class Meta:
        model = Food
        fields = ('name', 'tags', 'make_time', 'description', 'image')

    def create(self, data):
        tags = data.pop('tags')
        food = Food.objects.create(**data)
        for tag in tags:
            TagsFood.objects.create(tag=tag, food=food)
        return food


class FoodMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = ('id', 'name', 'image', 'make_time')
