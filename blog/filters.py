from django_filters.rest_framework import FilterSet
from .models import Post

class PostFilter(FilterSet):
    class Meta:
        model = Post
        fields = {
            'collection': ['exact']
        }

class OwnPostFilter(FilterSet):
    class Meta:
        model = Post
        fields = {
            'collection': ['exact'],
            'status': ['exact'],
            'is_private': ['exact']
        }    