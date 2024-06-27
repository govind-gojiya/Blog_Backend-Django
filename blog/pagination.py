from rest_framework.pagination import PageNumberPagination


class PostPagination(PageNumberPagination):
    page_size = 10
    

class PopularPostPagination(PageNumberPagination):
    page_size = 5


class FollowListPagination(PageNumberPagination):
    page_size = 25