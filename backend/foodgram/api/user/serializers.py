from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer as DjoserUserSerializer
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)

from user.models import Subscription
from api.common.serializers import RecipeMinifiedSerializer

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = DjoserUserSerializer.Meta.fields + ('avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.subscriptions_to_author.filter(user=request.user).exists()

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class SetAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance

    def create(self, validated_data):
        pass

    def to_representation(self, instance):
        return {'avatar': instance.avatar.url if instance.avatar else None}


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
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
        return UserSerializer(instance.author, context=self.context).data


class SubscriptionListSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(read_only=True, default=0)
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):

        fields = UserSerializer.Meta.fields + (
            'recipes_count',
            'recipes',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()

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


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
