from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.food.views import TagViewSet, IngredientViewSet, RecipeViewSet
from api.user.views import UserViewSet

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('s/<str:code>/', RecipeViewSet.as_view({'get': 'redirect_short_link'}), name='short-link-redirect'),
]