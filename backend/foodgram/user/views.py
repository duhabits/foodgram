from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from food.models import Recipe
from food.serializers import RecipeMinifiedSerializer
from food.pagination import StandardResultsSetPagination
from .models import Subscription
from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (permissions.AllowAny,)

    @action(detail=False, methods=('get',), permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


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

        serializer = UserSerializer(page, many=True, context={'request': request})
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

    @action(detail=True, methods=('post', 'delete'), url_path='subscribe')
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response({'errors': 'Нельзя подписаться на себя'}, status=400)
            Subscription.objects.get_or_create(user=user, author=author)
            data = UserSerializer(author, context={'request': request}).data
            recipes = Recipe.objects.filter(author=author)
            limit = request.query_params.get('recipes_limit')
            if limit:
                recipes = recipes[:int(limit)]
            data['recipes'] = RecipeMinifiedSerializer(recipes, many=True, context={'request': request}).data
            data['recipes_count'] = Recipe.objects.filter(author=author).count()
            return Response(data, status=201)

        count, _ = Subscription.objects.filter(user=user, author=author).delete()
        if count == 0:
            return Response({'errors': 'Подписки не было'}, status=400)
        return Response(status=204)