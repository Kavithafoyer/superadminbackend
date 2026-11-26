from rest_framework.pagination import PageNumberPagination


class FlexiblePageNumberPagination(PageNumberPagination):
    """Default DRF pagination with PAGE_SIZE=10 while honoring optional ?page_size= requests."""

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000
