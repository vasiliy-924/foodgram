from typing import Iterable, Optional
from io import BytesIO

from foodgram_backend.constants import SHOPPING_LIST_FORMAT


def build_absolute_file_url(request, file_field) -> Optional[str]:
    """Возвращает абсолютный URL для File/ImageField или None."""
    if not file_field:
        return None
    url = getattr(file_field, 'url', None)
    if not url:
        return None
    if request:
        try:
            return request.build_absolute_uri(url)
        except Exception:
            return url
    return url


def format_shopping_list(ingredients: Iterable[dict]) -> BytesIO:
    """Формирует файл со списком покупок в формате, заданном константой.

    Сейчас поддерживается только TXT; возвращается BytesIO с контентом.
    Структура входа: элементы с ключами 'name',
    'measurement_unit', 'total_amount'.
    """
    fmt = SHOPPING_LIST_FORMAT.lower()
    if fmt == 'txt':
        lines: list[str] = []
        for item in ingredients:
            name = item.get('name')
            unit = item.get('measurement_unit')
            amount = item.get('total_amount')
            lines.append(f'{name} ({unit}) — {amount}')
        content = '\n'.join(lines) or 'Список покупок пуст.'
        buffer = BytesIO()
        buffer.write(content.encode('utf-8'))
        buffer.seek(0)
        return buffer
    # Заглушка для будущих форматов (pdf и т.п.)
    raise ValueError('Unsupported shopping list format')
