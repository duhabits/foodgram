from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer
)
from food.fields import Base64ImageField

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
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
    avatar = Base64ImageField(required=True)


class SetAvatarResponseSerializer(serializers.Serializer):
    avatar = serializers.CharField(
        source='avatar.url',
        read_only=True
    )


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
