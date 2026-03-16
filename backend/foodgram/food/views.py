import io
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from django.http import FileResponse, HttpResponseRedirect, HttpResponseNotFound
from django.db.models import Sum
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Recipe, Tag, Ingredient, Favorite, ShoppingCart, RecipeIngredient, ShortLink
from .serializers import RecipeListSerializer, TagSerializer, IngredientSerializer, RecipeCreateUpdateSerializer, RecipeMinifiedSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', '')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('-id')
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        response_serializer = RecipeListSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        queryset = super().get_queryset()
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author_id=author)
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(favorites__user=self.request.user)
        is_in_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_cart == '1' and self.request.user.is_authenticated:
            queryset = queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    @action(detail=True, methods=['post', 'delete'], url_path='favorite', permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response({'errors': 'Рецепт уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted_count, _ = Favorite.objects.filter(user=user, recipe=recipe).delete()
        if not deleted_count:
            return Response({'errors': 'Рецепта не было в избранном'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart', permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            cart, created = ShoppingCart.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response({'errors': 'Рецепт уже в списке покупок'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted_count, _ = ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        if not deleted_count:
            return Response({'errors': 'Рецепта не было в списке покупок'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        short_link, created = ShortLink.objects.get_or_create(
            recipe=recipe,
            defaults={'code': ShortLink.generate_unique_code()}
        )
        short_url = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': short_url})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        format_type = request.query_params.get('format', 'txt').lower()
        cart_recipes = Recipe.objects.filter(shopping_cart__user=user)
        if not cart_recipes.exists():
            return Response({'errors': 'Список покупок пуст'}, status=status.HTTP_400_BAD_REQUEST)
        ingredients = RecipeIngredient.objects.filter(recipe__in=cart_recipes).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')
        if format_type == 'pdf':
            return self._generate_pdf_response(ingredients)
        elif format_type == 'csv':
            return self._generate_csv_response(ingredients)
        else:
            return self._generate_txt_response(ingredients)

    def _generate_txt_response(self, ingredients):
        buffer = io.BytesIO()
        buffer.write('СПИСОК ПОКУПОК\n'.encode('utf-8'))
        buffer.write('='.encode('utf-8') * 50 + '\n\n'.encode('utf-8'))
        for item in ingredients:
            line = f"□ {item['ingredient__name']} - {item['total_amount']} {item['ingredient__measurement_unit']}\n"
            buffer.write(line.encode('utf-8'))
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='shopping_list.txt', content_type='text/plain; charset=utf-8')

    def _generate_csv_response(self, ingredients):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])
        for item in ingredients:
            writer.writerow([item['ingredient__name'], item['total_amount'], item['ingredient__measurement_unit']])
        csv_content = buffer.getvalue().encode('utf-8')
        return FileResponse(io.BytesIO(csv_content), as_attachment=True, filename='shopping_list.csv', content_type='text/csv; charset=utf-8')

    def _generate_pdf_response(self, ingredients):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        p.setFont("Helvetica-Bold", 16)
        p.drawString(30 * mm, height - 20 * mm, "СПИСОК ПОКУПОК")
        p.line(30 * mm, height - 25 * mm, width - 30 * mm, height - 25 * mm)
        y = height - 35 * mm
        p.setFont("Helvetica", 12)
        for item in ingredients:
            if y < 30 * mm:
                p.showPage()
                p.setFont("Helvetica", 12)
                y = height - 20 * mm
            line = f"• {item['ingredient__name']} - {item['total_amount']} {item['ingredient__measurement_unit']}"
            p.drawString(30 * mm, y, line)
            y -= 8 * mm
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='shopping_list.pdf', content_type='application/pdf')


def redirect_short_link(request, code):
    try:
        short_link = ShortLink.objects.select_related('recipe').get(code=code)
        return HttpResponseRedirect(f'/recipes/{short_link.recipe.id}/')
    except ShortLink.DoesNotExist:
        return HttpResponseNotFound('Ссылка не найдена')