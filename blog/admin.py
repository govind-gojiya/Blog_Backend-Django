from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from . import models

@admin.register(models.Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'is_private', 'status', 'likes_count']
    list_editable = ['is_private']
    list_filter = ['is_private', 'status']
    list_select_related = ['owner', 'collection']
    list_per_page = 10

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).prefetch_related('liked_by')

    @admin.display()
    def likes_count(self, post):
        return post.number_of_likes()
    
admin.site.register(models.Collection)
admin.site.register(models.Follow)