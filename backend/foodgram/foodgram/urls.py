from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from food.views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    download_shopping_cart,
)
from user.views import (
    UserViewSet,
    SubscriptionViewSet,
    avatar_view,
    set_password,
)

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users', UserViewSet, basename='users')
router.register(
    r'users/subscriptions', SubscriptionViewSet, basename='subscriptions'
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # API endpoints
    path('api/', include(router.urls)),
    # Djoser endpoints (регистрация, логин и т.д.)
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    # Специфические endpoints для пользователей
    path('api/users/me/avatar/', avatar_view, name='user-avatar'),
    path('api/users/set_password/', set_password, name='set-password'),
    # Shopping cart download
    path(
        'api/recipes/download_shopping_cart/',
        download_shopping_cart,
        name='download-shop',
    ),
]

# Добавляем обработку медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
