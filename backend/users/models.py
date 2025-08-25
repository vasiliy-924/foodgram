from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram_backend.constants import STR_MAX_LENGTH, EMAIL_MAX_LENGTH
from users.validators import validate_username_value


class User(AbstractUser):
    """Модель пользователя с ролями и дополнительными полями."""

    class Roles(models.TextChoices):
        """Роли пользователя."""

        USER = 'user', 'Пользователь'
        ADMIN = 'admin', 'Администратор'

    first_name = models.CharField(
        verbose_name='имя',
        max_length=STR_MAX_LENGTH,
        blank=False
    )
    last_name = models.CharField(
        verbose_name='фамилия',
        max_length=STR_MAX_LENGTH,
        blank=False
    )
    username = models.CharField(
        verbose_name='никнейм',
        max_length=STR_MAX_LENGTH,
        unique=True,
        help_text=(
            f'Обязательно. Не более {STR_MAX_LENGTH} символов. '
            f'Только буквы, цифры и @/./+/-/_. '
        ),
        validators=(validate_username_value,),
        blank=False
    )
    email = models.EmailField(
        verbose_name='email адрес',
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        blank=False
    )
    role = models.CharField(
        verbose_name='роль',
        max_length=max(len(role) for role, _ in Roles.choices),
        choices=Roles.choices,
        default=Roles.USER
    )
    avatar = models.ImageField(
        verbose_name='аватар пользователя',
        blank=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    @property
    def is_admin(self):
        """Проверяет, является ли пользователь администратором."""
        return self.role == self.Roles.ADMIN or self.is_superuser

    def __str__(self):
        """Строковое представление пользователя."""
        return str(self.username)[:20]

    @property
    def is_subscribed(self):
        """Заглушка поля для сериализаторов (зависит от текущего пользов)."""
        return False
