from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from food.fields import Base64ImageField
from food.constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_USERNAME,
    MAX_LENGTH_FIRST_LAST_NAME,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""

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
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscribers.filter(user=request.user).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор создания пользователя."""

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )


class SetAvatarSerializer(serializers.Serializer):
    """Сериализатор установки аватара."""

    avatar = Base64ImageField(required=True)


class SetAvatarResponseSerializer(serializers.Serializer):
    """Сериализатор ответа с аватаром."""

    avatar = serializers.CharField(source='avatar.url', read_only=True)


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)