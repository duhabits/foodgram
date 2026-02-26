from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
import io
import csv
from .models import (
    Recipe,
    Tag,
    Ingredient,
    Favorite,
    ShoppingCart,
    RecipeIngredient,
)
from .serializers import (
    RecipeListSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Пагинация для списка рецептов"""

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов"""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Поиск по имени ингредиента"""
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', '')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов"""

    queryset = Recipe.objects.all().order_by('-id')
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def get_permissions(self):
        """Настройка прав доступа"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        """Сохранение автора при создании"""
        serializer.save(author=self.request.user)

    def get_queryset(self):
        """Фильтрация рецептов"""
        queryset = super().get_queryset()

        # Фильтрация по тегам
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        # Фильтрация по автору
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author_id=author)

        # Фильтрация по избранному
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(favorites__user=self.request.user)

        # Фильтрация по списку покупок
        is_in_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_cart == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(shopping_cart__user=self.request.user)

        return queryset

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление из избранного"""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted = Favorite.objects.filter(
                user=user, recipe=recipe
            ).delete()[0]
            if not deleted:
                return Response(
                    {'errors': 'Рецепта не было в избранном'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление из списка покупок"""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            cart, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted = ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).delete()[0]
            if not deleted:
                return Response(
                    {'errors': 'Рецепта не было в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт"""
        recipe = self.get_object()
        # Простая реализация короткой ссылки
        short_link = f"{request.build_absolute_uri('/')}s/{recipe.id}"
        return Response({'short-link': short_link})


@action(
    detail=False,
    methods=['get'],
    permission_classes=[permissions.IsAuthenticated],
)
def download_shopping_cart(request):
    """Скачивание списка покупок"""
    user = request.user

    # Получаем все рецепты из корзины пользователя
    cart_recipes = Recipe.objects.filter(shopping_cart__user=user)

    # Собираем все ингредиенты
    ingredients = (
        RecipeIngredient.objects.filter(recipe__in=cart_recipes)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )

    # Создаем файл
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Список покупок'])
    writer.writerow([])

    for ingredient in ingredients:
        writer.writerow(
            [
                ingredient['ingredient__name'],
                f"{ingredient['total_amount']} {ingredient['ingredient__measurement_unit']}",
            ]
        )

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename='shopping_list.txt',
        content_type='text/plain',
    )
