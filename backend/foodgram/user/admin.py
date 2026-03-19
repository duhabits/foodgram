from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError

from .models import User, Subscription


@admin.register(User)
class UserAdmin(UserAdmin):

    list_display = (
        'id', 'username', 'email',
        'first_name', 'last_name', 'is_staff'
    )
    list_display_links = ('id', 'username')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'email', 'avatar')
        }),
        ('Права доступа', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name',
                'last_name', 'password1', 'password2'
            ),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'author')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'author__username')

    def save_model(self, request, obj, form, change):
        if obj.user == obj.author:
            raise ValidationError('Нельзя подписаться на самого себя.')
        super().save_model(request, obj, form, change)
