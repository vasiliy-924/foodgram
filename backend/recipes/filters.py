from django.contrib import admin

from foodgram_backend.constants import (
    COOKING_TIME_FAST_MAX,
    COOKING_TIME_LONG_THRESHOLD,
    COOKING_TIME_MEDIUM_MIN,
    COOKING_TIME_MEDIUM_MAX,
    MIN_COOKING_TIME_MINUTES,
)


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр по времени готовки рецепта."""

    title = 'Время готовки'
    parameter_name = 'cooking_time_group'

    def lookups(self, request, model_admin):
        return [
            (
                'fast',
                (
                    f'Быстрые (от {MIN_COOKING_TIME_MINUTES} до '
                    f'{COOKING_TIME_FAST_MAX} минут)'
                ),
            ),
            (
                'medium',
                (
                    f'Средние (от {COOKING_TIME_MEDIUM_MIN} минут до '
                    f'{COOKING_TIME_MEDIUM_MAX} минут)'
                ),
            ),
            (
                'long',
                f'Долгие (больше {COOKING_TIME_LONG_THRESHOLD} минут)',
            ),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'fast':
            return queryset.filter(
                cooking_time__gte=MIN_COOKING_TIME_MINUTES,
                cooking_time__lte=COOKING_TIME_FAST_MAX,
            )
        if value == 'medium':
            return queryset.filter(
                cooking_time__gte=COOKING_TIME_MEDIUM_MIN,
                cooking_time__lte=COOKING_TIME_MEDIUM_MAX,
            )
        if value == 'long':
            return queryset.filter(
                cooking_time__gt=COOKING_TIME_LONG_THRESHOLD
            )
        return queryset
