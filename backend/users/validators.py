import re

from rest_framework import serializers

USERNAME_REGEX = r'^[\w.@+-]+\Z'


def validate_username_value(value: str) -> str:
    """Валидирует username по regex."""
    if not re.fullmatch(USERNAME_REGEX, value):
        raise serializers.ValidationError(
            'Имя пользователя содержит запрещённые символы.'
        )
    return value
