from typing import Optional


def build_absolute_file_url(request, file_field) -> Optional[str]:
    """
    Возвращает абсолютный URL для File/ImageField
    или None, если файла нет.
    """
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
