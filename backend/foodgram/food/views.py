import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from django.http import FileResponse, HttpResponseRedirect, HttpResponseNotFound
from django.db.models import Sum
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Recipe, Tag, Ingredient, Favorite, ShoppingCart, RecipeIngredient, ShortLink
from .serializers import (
    RecipeListSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
)
from .filters import RecipeFilter
from .pagination import StandardResultsSetPagination
from .constants import MAX_LENGTH_SHORT_CODE


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

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if name:
            return self.queryset.filter(name__istartswith=name)
        return self.queryset


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
        full_serializer = RecipeListSerializer(serializer.instance, context={'request': request})
        return Response(full_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=('post', 'delete'), permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            _, created = Favorite.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response({'errors': 'Рецепт уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)
            return Response(RecipeMinifiedSerializer(recipe).data, status=status.HTTP_201_CREATED)
        count, _ = Favorite.objects.filter(user=user, recipe=recipe).delete()
        if count == 0:
            return Response({'errors': 'Рецепта не было в избранном'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post', 'delete'), permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            _, created = ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response({'errors': 'Рецепт уже в списке покупок'}, status=status.HTTP_400_BAD_REQUEST)
            return Response(RecipeMinifiedSerializer(recipe).data, status=status.HTTP_201_CREATED)
        count, _ = ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        if count == 0:
            return Response({'errors': 'Рецепта не было в списке покупок'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('get',))
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link, _ = ShortLink.objects.get_or_create(
            recipe=recipe,
            defaults={'code': ShortLink.generate_unique_code(length=MAX_LENGTH_SHORT_CODE)}
        )
        full_url = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': full_url})

    @action(detail=False, methods=('get',), permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        recipes = Recipe.objects.filter(shopping_cart__user=user)
        if not recipes.exists():
            return Response({'errors': 'Список покупок пуст'}, status=status.HTTP_400_BAD_REQUEST)

        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        y = h - 40 * mm
        p.setFont('Helvetica-Bold', 16)
        p.drawString(30 * mm, h - 20 * mm, 'Список покупок')
        p.line(30 * mm, h - 25 * mm, w - 30 * mm, h - 25 * mm)
        p.setFont('Helvetica', 12)

        for ing in ingredients:
            if y < 30 * mm:
                p.showPage()
                y = h - 20 * mm
            text = f"• {ing['ingredient__name']} — {ing['total_amount']} {ing['ingredient__measurement_unit']}"
            p.drawString(30 * mm, y, text)
            y -= 10 * mm

        p.save()
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_list.pdf',
            content_type='application/pdf'
        )


def redirect_short_link(request, code):
    try:
        link = ShortLink.objects.select_related('recipe').get(code=code)
        return HttpResponseRedirect(f'/recipes/{link.recipe.id}/')
    except ShortLink.DoesNotExist:
        return HttpResponseNotFound('Ссылка не найдена.')