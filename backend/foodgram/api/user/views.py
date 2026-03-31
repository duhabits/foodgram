from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from api.food.serializers import RecipeMinifiedSerializer
from api.pagination import StandardResultsSetPagination
from api.user.serializers import (
    SetAvatarSerializer,
    UserSerializer,
    SubscriptionSerializer,
    SubscriptionListSerializer,
)
from food.models import Recipe
from user.models import Subscription

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (permissions.AllowAny,)

    @action(
        detail=False,
        methods=('get',),
        url_path='subscriptions',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            subscribers__user=request.user
        ).annotate(recipes_count=Count('recipes'))

        page = self.paginate_queryset(queryset)
        serializer = SubscriptionListSerializer(
            page, many=True, context={'request': request}
        )

        return self.get_paginated_response(serializer.data)


@action(
    detail=True,
    methods=('post', 'delete'),
    url_path='subscribe',
    permission_classes=(permissions.IsAuthenticated,),
)
def subscribe(self, request, pk=None):
    if request.method == 'POST':
        data = {'user': request.user.id, 'author': pk}
        serializer = SubscriptionSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()

        return Response(
            serializer.to_representation(subscription),
            status=status.HTTP_201_CREATED,
        )


@subscribe.mapping.delete
def delete_subscribe(self, request, pk=None):
    deleted_count, _ = Subscription.objects.filter(
        user=request.user, author=pk
    ).delete()

    if deleted_count == 0:
        return Response(
            {'errors': 'Вы не были подписаны на этого пользователя.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)


@action(
    detail=False,
    methods=('put', 'delete'),
    url_path='me/avatar',
    permission_classes=(permissions.IsAuthenticated,),
)
def avatar(self, request):
    user = request.user

    if request.method == 'PUT':
        serializer = SetAvatarSerializer(
            instance=user, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = SetAvatarSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@avatar.mapping.delete
def delete_avatar(self, request):
    user = request.user

    if user.avatar:
        user.avatar.delete(save=False)
        user.avatar = None
        user.save()

    return Response(status=status.HTTP_204_NO_CONTENT)
