from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from api.food.filters import RecipeFilter
from api.food.serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeListSerializer,
    RecipeMinifiedSerializer,
    TagSerializer,
)
from api.pagination import StandardResultsSetPagination
from core.constants import MAX_LENGTH_SHORT_CODE
from food.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShortLink,
    Tag,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)

    filter_backends = (SearchFilter,)

    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    pagination_class = StandardResultsSetPagination
    permission_classes = (permissions.AllowAny,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        full_serializer = RecipeListSerializer(
            serializer.instance, context={'request': request}
        )
        return Response(
            full_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            _, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                RecipeMinifiedSerializer(recipe).data,
                status=status.HTTP_201_CREATED,
            )
        count, _ = Favorite.objects.filter(user=user, recipe=recipe).delete()
        if count == 0:
            return Response(
                {'errors': 'Рецепта не было в избранном'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            _, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                RecipeMinifiedSerializer(recipe).data,
                status=status.HTTP_201_CREATED,
            )
        count, _ = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if count == 0:
            return Response(
                {'errors': 'Рецепта не было в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('get',))
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link, _ = ShortLink.objects.get_or_create(
            recipe=recipe,
            defaults={
                'code': ShortLink.generate_unique_code(
                    length=MAX_LENGTH_SHORT_CODE
                )
            },
        )
        short_url_path = reverse(
            'short-link-redirect', args=(short_link.code,)
        )
        short_url = request.build_absolute_uri(short_url_path)
        return Response({'short-link': short_url})

    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        user = request.user
        recipes = Recipe.objects.filter(shopping_cart__user=user)

        if not recipes.exists():
            return Response(
                {'error': 'Корзина покупок пуста'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )

        lines = ['Список покупок\n', '=' * 50 + '\n\n']

        for ingredient in ingredients:
            lines.append(
                f"{ingredient['ingredient__name']} - "
                f"{ingredient['total_amount']} "
                f"{ingredient['ingredient__measurement_unit']}\n"
            )

        lines.append('\n' + '=' * 50)
        lines.append(f'\nВсего позиций: {len(ingredients)}')

        response.content = ''.join(lines)

        return response


def short_link_redirect(request, code):
    short_link = get_object_or_404(ShortLink, code=code)
    recipe = short_link.recipe
    return redirect(f'/recipes/{recipe.id}/')
