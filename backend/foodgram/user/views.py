from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from food.models import Recipe
from food.serializers import RecipeMinifiedSerializer
from food.pagination import StandardResultsSetPagination
from .models import Subscription
from .serializers import (
    UserSerializer,
    SetAvatarSerializer,
    SetAvatarResponseSerializer,
    SetPasswordSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (permissions.AllowAny,)

    @action(detail=False, permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)


class SubscriptionViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return User.objects.filter(subscribers__user=self.request.user)

    def list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        if page is None:
            return Response([])

        serializer = self.get_serializer(page, many=True, context={'request': request})
        result = []

        for user_data, user in zip(serializer.data, page):
            recipes = Recipe.objects.filter(author=user)
            limit = request.query_params.get('recipes_limit')
            if limit:
                recipes = recipes[:int(limit)]

            user_data['recipes'] = RecipeMinifiedSerializer(
                recipes, many=True, context={'request': request}
            ).data
            user_data['recipes_count'] = Recipe.objects.filter(author=user).count()
            result.append(user_data)

        return self.get_paginated_response(result)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response({'errors': 'Нельзя подписаться на себя'}, status=400)

            Subscription.objects.get_or_create(user=user, author=author)
            data = self.get_serializer(author, context={'request': request}).data

            recipes = Recipe.objects.filter(author=author)
            limit = request.query_params.get('recipes_limit')
            if limit:
                recipes = recipes[:int(limit)]

            data['recipes'] = RecipeMinifiedSerializer(
                recipes, many=True, context={'request': request}
            ).data
            data['recipes_count'] = Recipe.objects.filter(author=author).count()

            return Response(data, status=201)

        deleted_count, _ = Subscription.objects.filter(user=user, author=author).delete()
        if not deleted_count:
            return Response({'errors': 'Подписки не было'}, status=400)

        return Response(status=204)


@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def avatar_view(request):
    """Добавление или удаление аватара текущего пользователя"""
    user = request.user

    if request.method == 'PUT':
        serializer = SetAvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if user.avatar:
            user.avatar.delete(save=False)

        user.avatar = serializer.validated_data['avatar']
        user.save()

        response_serializer = SetAvatarResponseSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def set_password(request):
    """Смена пароля текущего пользователя"""
    serializer = SetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user

    if not user.check_password(serializer.validated_data['current_password']):
        return Response(
            {'current_password': ['Неверный пароль']},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(serializer.validated_data['new_password'])
    user.save()

    return Response(status=status.HTTP_204_NO_CONTENT)