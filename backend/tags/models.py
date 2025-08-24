from django.db import models

from foodgram_backend.constants import (
    TAG_NAME_MAX_LENGTH,
    SLUG_MAX_LENGTH,
)


class Tag(models.Model):
    """Модель тега рецепта."""

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return str(self.name)
