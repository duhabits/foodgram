from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from .models import Ingredient, Tags, Food
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    FoodSerializer,
    FoodCreateSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]


class FoodViewSet(viewsets.ModelViewSet):

    queryset = Food.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return FoodSerializer
        return FoodCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
