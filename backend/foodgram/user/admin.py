from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from .models import Subscription, User


@admin.register(User)
class UserAdmin(UserAdmin):

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'recipes_count',
        'subscribers_count',
        'is_staff',
    )
    list_display_links = ('id', 'username')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_count=Count('recipes', distinct=True),
            subscribers_count=Count('subscribers', distinct=True),
        )

    def recipes_count(self, obj):
        return obj.recipes_count

    recipes_count.short_description = 'Кол-во рецептов'
    recipes_count.admin_order_field = 'recipes_count'

    def subscribers_count(self, obj):
        return obj.subscribers_count

    subscribers_count.short_description = 'Подписчиков'
    subscribers_count.admin_order_field = 'subscribers_count'

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (
            'Персональная информация',
            {'fields': ('first_name', 'last_name', 'email', 'avatar')},
        ),
        (
            'Права доступа',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'password1',
                    'password2',
                ),
            },
        ),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'author')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'author__username')
