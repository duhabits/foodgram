from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""

    is_subscribed = serializers.SerializerMethodField()

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


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя"""

    class Meta(UserCreateSerializer.Meta):
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
    """Сериализатор установки аватара"""

    avatar = serializers.ImageField()


class SetAvatarResponseSerializer(serializers.Serializer):
    """Сериализатор ответа с аватаром"""

    avatar = serializers.CharField(source='avatar.url')


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля"""

    current_password = serializers.CharField()
    new_password = serializers.CharField()
