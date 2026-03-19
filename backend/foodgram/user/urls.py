from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    SubscriptionViewSet,
    avatar_view,
    set_password,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'users/subscriptions/',
        SubscriptionViewSet.as_view({'get': 'list'}),
        name='subscriptions',
    ),
    path(
        'users/<int:pk>/subscribe/',
        SubscriptionViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}),
        name='subscribe',
    ),
    path('users/me/avatar/', avatar_view, name='user-avatar'),
    path('users/set_password/', set_password, name='set-password'),
]