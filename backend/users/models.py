from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from foodgram_backend.constants import (
    EMAIL_MAX_LENGTH,
    STR_REPRESENTATION_MAX_LENGTH,
    USER_FIELD_MAX_LENGTH,
)
from users.validators import validate_username_value


class User(AbstractUser):
    """Модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    first_name = models.CharField(
        verbose_name='имя',
        max_length=USER_FIELD_MAX_LENGTH
    )
    last_name = models.CharField(
        verbose_name='фамилия',
        max_length=USER_FIELD_MAX_LENGTH
    )
    username = models.CharField(
        verbose_name='никнейм',
        max_length=USER_FIELD_MAX_LENGTH,
        unique=True,
        help_text=(
            f'Обязательно. Не более {USER_FIELD_MAX_LENGTH} символов. '
            f'Только буквы, цифры и @/./+/-/_. '
        ),
        validators=(validate_username_value,)
    )
    email = models.EmailField(
        verbose_name='email адрес',
        max_length=EMAIL_MAX_LENGTH,
        unique=True
    )
    avatar = models.ImageField(
        verbose_name='аватар пользователя',
        blank=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        """Строковое представление пользователя."""
        return self.username[:STR_REPRESENTATION_MAX_LENGTH]


class Subscription(models.Model):
    """Подписка пользователя на автора рецептов."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions_to_author',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription'
            ),
        )

    def clean(self):
        """Запрещает подписку пользователя на самого себя (валидация формы)."""
        same_user = self.user is not None and self.author is not None and (
            self.user == self.author
        )
        if same_user:
            raise ValidationError({'author': 'Нельзя подписаться на себя.'})

    def __str__(self):
        """Возвращает отображаемое имя автора подписки."""
        return str(self.author)[:STR_REPRESENTATION_MAX_LENGTH]
