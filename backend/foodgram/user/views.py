from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet

from food.models import Recipe
from food.serializers import RecipeMinifiedSerializer
from .models import Subscription
from .serializers import (
    UserSerializer,
    CustomUserCreateSerializer,
    SetAvatarSerializer,
    SetAvatarResponseSerializer,
    SetPasswordSerializer,
)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return UserSerializer


class SubscriptionViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(subscribers__user=self.request.user)

    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = UserSerializer(page, many=True, context={'request': request})
        result_data = []
        for item, user in zip(serializer.data, page):
            recipes = Recipe.objects.filter(author=user)
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                recipes = recipes[:int(recipes_limit)]
            item['recipes'] = RecipeMinifiedSerializer(recipes, many=True, context={'request': request}).data
            item['recipes_count'] = Recipe.objects.filter(author=user).count()
            result_data.append(item)
        return self.get_paginated_response(result_data)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        user = request.user
        if request.method == 'POST':
            if user == author:
                return Response({'errors': 'Нельзя подписаться на самого себя'}, status=status.HTTP_400_BAD_REQUEST)
            Subscription.objects.get_or_create(user=user, author=author)
            serializer = UserSerializer(author, context={'request': request})
            data = serializer.data
            recipes = Recipe.objects.filter(author=author)
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                recipes = recipes[:int(recipes_limit)]
            data['recipes'] = RecipeMinifiedSerializer(recipes, many=True, context={'request': request}).data
            data['recipes_count'] = Recipe.objects.filter(author=author).count()
            return Response(data, status=status.HTTP_201_CREATED)
        deleted = Subscription.objects.filter(user=user, author=author).delete()[0]
        if not deleted:
            return Response({'errors': 'Вы не были подписаны на этого пользователя'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def avatar_view(request):
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
    serializer = SetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = request.user
    if not user.check_password(serializer.validated_data['current_password']):
        return Response({'current_password': ['Неверный пароль']}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    return Response(status=status.HTTP_204_NO_CONTENT)