from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.contenttypes.admin import GenericTabularInline
from blog.admin import PostAdmin
from blog.models import Post
from tags.models import TaggedItem
from . import models


class TagsInline(GenericTabularInline):
    model = TaggedItem
    autocomplete_fields = ['tag']


class CustomPostAdmin(PostAdmin):
    inlines = [TagsInline]


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email']

admin.site.register(models.Role)
# admin.site.register(models.User)
admin.site.unregister(Post)
admin.site.register(Post, CustomPostAdmin)
