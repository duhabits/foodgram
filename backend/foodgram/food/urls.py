from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    redirect_short_link,
)

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('s/<str:code>/', redirect_short_link, name='short-link-redirect'),
]
