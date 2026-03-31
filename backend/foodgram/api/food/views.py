from django.db.models import Sum
from django.http import FileResponse, HttpResponsePermanentRedirect
from django.urls import reverse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from api.food.filters import RecipeFilter
from api.food.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeListSerializer,
    RecipeMinifiedSerializer,
    ShoppingCartSerializer,
    TagSerializer,
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
    pagination_class = None
    permission_classes = (permissions.AllowAny,)

    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (
        Recipe.objects.select_related('author')
        .prefetch_related('tags', 'recipe_ingredients__ingredient')
        .order_by('-created_at')
    )
    pagination_class = StandardResultsSetPagination
    permission_classes = (permissions.AllowAny,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_relation(
        self,
        request,
        pk,
        model,
        serializer_class,
        error_message,
    ):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = serializer_class(
                data=data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                RecipeMinifiedSerializer(recipe).data,
                status=status.HTTP_201_CREATED,
            )

        deleted_count, _ = model.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if deleted_count == 0:
            return Response(
                {'errors': error_message}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self._handle_relation(
            request,
            pk,
            Favorite,
            FavoriteSerializer,
            'Рецепта не было в избранном',
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_relation(
            request,
            pk,
            ShoppingCart,
            ShoppingCartSerializer,
            'Рецепта не было в списке покупок',
        )

    @action(detail=True, methods=('get',), url_path='get_link')
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
            reverse('short_link_redirect', args=[short_link.code])
        )
        return Response({'short-link': short_url})

    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        if not ingredients.exists():
            return Response(
                {'error': 'Корзина покупок пуста'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        content = generate_shopping_cart_content(ingredients)
        response = FileResponse(
            content,
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename='shopping_cart.txt',
        )
        return response


def short_link_redirect(request, code):
    try:
        short_link = ShortLink.objects.get(code=code)
        redirect_url = reverse('recipe_detail', args=[short_link.recipe.id])
    except ShortLink.DoesNotExist:
        redirect_url = reverse('not_found')

    return HttpResponsePermanentRedirect(
        request.build_absolute_uri(redirect_url)
    )
