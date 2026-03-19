from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

from food.constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_FIRST_LAST_NAME,
    MAX_LENGTH_USERNAME,
)


class User(AbstractUser):

    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_LAST_NAME,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_LAST_NAME,
        verbose_name='Фамилия',
    )

    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        verbose_name='Email',
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        verbose_name='Аватар',
        null=True,
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription',
            )
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} → {self.author.username}'
