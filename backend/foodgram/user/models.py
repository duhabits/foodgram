from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class MyUser(AbstractUser):
    """Кастомная модель пользователя"""

    email = models.EmailField(
        max_length=254, unique=True, verbose_name='Email'
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
    """Подписки на авторов"""
    user = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='subscriptions'
    )
    author = models.ForeignKey(
        MyUser, on_delete=models.CASCADE, related_name='subscribers'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            )
        ]

    def clean(self):
        if self.user == self.author:
            raise ValidationError("Нельзя подписаться на самого себя")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} -> {self.author.username}"