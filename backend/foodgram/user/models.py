from django.contrib.auth.models import AbstractUser
from django.db import models


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
