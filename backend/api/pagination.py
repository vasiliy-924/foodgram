from rest_framework.pagination import PageNumberPagination
from foodgram_backend.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class LimitPageNumberPagination(PageNumberPagination):
    """Нумерация страниц с параметрами page и limit (по умолчанию 6)."""

    page_size = DEFAULT_PAGE_SIZE
    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
