from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField

from user.models import Subscription
from food.models import Recipe
from api.common.serializers import RecipeMinifiedSerializer

User = get_user_model()


class SetAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)

    def to_representation(self, instance):
        """Форматируем ответ после сохранения аватара"""
        return {'avatar': instance.avatar.url if instance.avatar else None}


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        """Проверка: нельзя подписаться на самого себя"""
        request = self.context.get('request')
        user = request.user
        author = data['author']

        if user == author:
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на самого себя.'}
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {'errors': 'Вы уже подписаны на этого пользователя.'}
            )

        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        author = instance.author

        from api.user.serializers import UserSerializer

        representation = UserSerializer(
            author, context={'request': request}
        ).data

        recipes = Recipe.objects.filter(author=author)
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[: int(recipes_limit)]

        representation['recipes'] = RecipeMinifiedSerializer(
            recipes, many=True, context={'request': request}
        ).data
        representation['recipes_count'] = Recipe.objects.filter(
            author=author
        ).count()

        return representation


class SubscriptionListSerializer(serializers.ModelSerializer):
    recipes_count = serializers.IntegerField(read_only=True)
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes_count',
            'recipes',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = Recipe.objects.filter(author=obj)

        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    recipes_limit = int(recipes_limit)
                    recipes = recipes[:recipes_limit]
                except (ValueError, TypeError):
                    pass

        return RecipeMinifiedSerializer(
            recipes, many=True, context={'request': request}
        ).data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscribers.filter(user=request.user).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None
