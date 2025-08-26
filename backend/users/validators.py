import re

from rest_framework import serializers

from foodgram_backend.constants import FORBIDDEN_USERNAME

USERNAME_REGEX = r'^[\w.@+-]+\Z'


def validate_username_value(value: str) -> str:
    """Валидирует username по regex и запрещает специальное имя `me`."""
    if not re.fullmatch(USERNAME_REGEX, value):
        raise serializers.ValidationError(
            'Имя пользователя содержит запрещённые символы.'
        )
    if value.lower() == FORBIDDEN_USERNAME:
        raise serializers.ValidationError(
            f'Username {FORBIDDEN_USERNAME} запрещён.'
        )
    return value
