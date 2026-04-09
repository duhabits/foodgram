from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from api.pagination import StandardResultsSetPagination
from api.user.serializers import (
    SetAvatarSerializer,
    SubscriptionCreateSerializer,
    SubscriptionListSerializer,
)
from user.models import Subscription
from api.user.serializers import UserSerializer

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
        queryset = (
            User.objects.filter(authors__user=request.user)
            .annotate(recipes_count=Count('recipes'))
            .order_by('username')
        )

        page = self.paginate_queryset(queryset)
        serializer = SubscriptionListSerializer(
            page, many=True, context={'request': request}
        )

        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        url_path='subscribe',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        data = {'user': request.user.id, 'author': id}
        serializer = SubscriptionCreateSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        deleted_count, _ = Subscription.objects.filter(
            user=request.user, author=id
        ).delete()

        if not deleted_count:
            return Response(
                {'errors': 'Вы не были подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def avatar(self, request):
        user = request.user

        serializer = SetAvatarSerializer(
            instance=user, data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
