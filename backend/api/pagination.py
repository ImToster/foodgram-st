from rest_framework.pagination import PageNumberPagination

import const


class CustomPagination(PageNumberPagination):
    page_size_query_param = const.PAGE_SIZE_QUERY_PARAM
    page_size = const.PAGE_SIZE
    max_page_size = const.MAX_PAGE_SIZE
