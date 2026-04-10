from django.db.models import Sum
from django.http import FileResponse, HttpResponsePermanentRedirect
from django.urls import reverse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from api.food.filters import RecipeFilter, IngredientFilter
from api.food.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    RecipeListSerializer,
)
from api.food.utils import generate_shopping_cart_content
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
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


# ... (твои импорты остаются без изменений)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'recipe_ingredients__ingredient'
    )
    pagination_class = StandardResultsSetPagination
    permission_classes = (permissions.AllowAny,)
    filterset_class = RecipeFilter
    # Добавляем фильтрацию (обязательно для работы избранного и корзины в списке)
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeListSerializer
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _create_relation(self, recipe, serializer_class):
        data = {'user': self.request.user.id, 'recipe': recipe.id}
        serializer = serializer_class(
            data=data, context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_relation(self, recipe, model, error_message):
        deleted_count, _ = model.objects.filter(
            user=self.request.user, recipe=recipe
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': error_message}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self._create_relation(recipe, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = self.get_object()
        return self._delete_relation(
            recipe, Favorite, 'Рецепта не было в избранном'
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self._create_relation(recipe, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self._delete_relation(
            recipe, ShoppingCart, 'Рецепта не было в списке покупок'
        )

    @action(detail=True, methods=('get',), url_path='get-link')
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
        short_url = request.build_absolute_uri(
            reverse('short-link-redirect', args=[short_link.code])
        )
        return Response({'short-link': short_url})

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__in_shopping_carts__user=request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        content = generate_shopping_cart_content(ingredients)
        response = FileResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


def short_link_redirect(request, code):
    try:
        short_link = ShortLink.objects.get(code=code)
        return HttpResponsePermanentRedirect(
            f'/recipes/{short_link.recipe.id}/'
        )
    except ShortLink.DoesNotExist:
        return HttpResponsePermanentRedirect('/')
