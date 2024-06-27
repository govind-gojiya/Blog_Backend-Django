from ckeditor.fields import RichTextField
from django.conf import settings
from django.db import models
from .validators import validate_file_size
from hitcount.models import HitCountMixin, HitCount
from django.contrib.contenttypes.fields import GenericRelation
import hitcount

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class Collection(models.Model):
    label = models.CharField(max_length=255)

    class Meta:
        ordering = ['label']

    def __str__(self) -> str:
        return self.label
    
    def __repr__(self) -> str:
        return self.label


class Post(TimeStampedModel, HitCountMixin):
    NOT_REQUESTED = 0
    REQUESTED = 1
    APPROVED = 2
    DECLINED = 3
    POST_STATUS = [
        (NOT_REQUESTED, 'Not request yet'),
        (REQUESTED, 'Request for public'),
        (APPROVED, 'Approved post'),
        (DECLINED, 'Declined post'),
    ]

    post_id = models.BigAutoField(primary_key=True, unique=True)
    title = models.CharField(max_length=255)
    content = RichTextField()
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='blogs/thumbnail', null=True, blank=True)
    is_private = models.BooleanField(default=True)
    status = models.SmallIntegerField(choices=POST_STATUS, default=NOT_REQUESTED)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='posts', on_delete=models.CASCADE, null=False, blank=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    likes_count = models.PositiveIntegerField(default=0)
    hit_count_generic = GenericRelation(HitCount, object_id_field='object_p',
                                        related_query_name='hit_count_generic_relation')
    collection = models.ForeignKey(Collection, related_name='posts', on_delete=models.PROTECT)


class SavedPost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='savedpost')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post') 


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follower', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
