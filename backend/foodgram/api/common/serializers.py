from django.contrib.auth import get_user_model
from rest_framework import serializers

from food.models import Recipe

User = get_user_model()


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None
