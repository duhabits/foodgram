from django.urls import path, include
from rest_framework.routers import DefaultRouter
from food.views import TagViewSet, IngredientViewSet, FoodViewSet

router = DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', FoodViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include('djoser.urls')),
    path('api/', include('djoser.urls.authtoken')),
]
