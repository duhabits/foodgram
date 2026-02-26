from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from food.models import Subscription, Recipe  # Изменено с Food на Recipe
from food.serializers import (
    RecipeMinifiedSerializer,
)  # Изменено с FoodMinifiedSerializer
from .serializers import (
    UserSerializer,
    SetAvatarSerializer,
    SetPasswordSerializer,
)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    """Пагинация для списка пользователей"""

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для пользователей"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        """Получение текущего пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class SubscriptionViewSet(viewsets.GenericViewSet):
    """Вьюсет для подписок"""

    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Получение списка подписок"""
        return User.objects.filter(subscribers__user=self.request.user)

    def list(self, request):
        """Список подписок текущего пользователя"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes_limit = int(recipes_limit)

        serializer = self.get_serializer(
            page, many=True, context={'request': request}
        )

        # Добавляем рецепты и количество
        result_data = []
        for user_data, user_instance in zip(serializer.data, page):
            recipes = Recipe.objects.filter(
                author=user_instance
            )  # Изменено с Food на Recipe
            if recipes_limit:
                recipes = recipes[:recipes_limit]

            user_data['recipes'] = (
                RecipeMinifiedSerializer(  # Изменено с FoodMinifiedSerializer
                    recipes, many=True, context={'request': request}
                ).data
            )
            user_data['recipes_count'] = (
                Recipe.objects.filter(  # Изменено с Food на Recipe
                    author=user_instance
                ).count()
            )
            result_data.append(user_data)

        return self.get_paginated_response(result_data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        """Подписка/отписка на пользователя"""
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author
            )

            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = UserSerializer(author, context={'request': request})
            data = serializer.data

            # Добавляем рецепты и количество
            recipes = Recipe.objects.filter(
                author=author
            )  # Изменено с Food на Recipe
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                recipes = recipes[: int(recipes_limit)]

            data['recipes'] = (
                RecipeMinifiedSerializer(  # Изменено с FoodMinifiedSerializer
                    recipes, many=True, context={'request': request}
                ).data
            )
            data['recipes_count'] = (
                Recipe.objects.filter(  # Изменено с Food на Recipe
                    author=author
                ).count()
            )

            return Response(data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted = Subscription.objects.filter(
                user=user, author=author
            ).delete()[0]

            if not deleted:
                return Response(
                    {'errors': 'Вы не были подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(status=status.HTTP_204_NO_CONTENT)


@action(
    detail=False,
    methods=['put', 'delete'],
    permission_classes=[permissions.IsAuthenticated],
)
def avatar_view(request):
    """Управление аватаром пользователя"""
    user = request.user

    if request.method == 'PUT':
        serializer = SetAvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Удаляем старый аватар
        if user.avatar:
            user.avatar.delete()

        user.avatar = serializer.validated_data['avatar']
        user.save()

        return Response(
            {'avatar': request.build_absolute_uri(user.avatar.url)}
        )

    elif request.method == 'DELETE':
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


@action(
    detail=False,
    methods=['post'],
    permission_classes=[permissions.IsAuthenticated],
)
def set_password(request):
    """Смена пароля"""
    serializer = SetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user

    if not user.check_password(serializer.validated_data['current_password']):
        return Response(
            {'current_password': ['Неверный пароль']},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(serializer.validated_data['new_password'])
    user.save()

    return Response(status=status.HTTP_204_NO_CONTENT)
