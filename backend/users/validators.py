import re

from rest_framework import serializers

from foodgram_backend.constants import FORBIDDEN_USERNAME

USERNAME_REGEX = r'^[\w.@+-]+\Z'


def validate_username_value(value):
    """Проверяет корректность username по шаблону и запрещает me."""
    forbidden = re.sub(r'[\w.@+-]', '', value)
    if forbidden:
        raise serializers.ValidationError(
            f'Имя пользователя содержит запрещённые символы: {set(forbidden)}'
        )
    if value.lower() == FORBIDDEN_USERNAME:
        raise serializers.ValidationError(
            f'Username {FORBIDDEN_USERNAME} запрещён.'
        )
    return value
