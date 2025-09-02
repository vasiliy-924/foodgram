from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.db import models

from foodgram_backend.constants import STR_MAX_LENGTH, EMAIL_MAX_LENGTH
from users.validators import validate_username_value


class User(AbstractUser):
    """Модель пользователя."""

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
    avatar = models.ImageField(
        verbose_name='аватар пользователя',
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        """Строковое представление пользователя."""
        return str(self.username)[:20]

    @property
    def is_subscribed(self):
        """Заглушка поля для сериализаторов (зависит от текущего пользов)."""
        return False

    def set_password(self, raw_password):
        """Устанавливает пароль после проверки встроенными валидаторами."""
        if raw_password is None:
            return super().set_password(raw_password)
        validate_password(raw_password, user=self)
        return super().set_password(raw_password)
