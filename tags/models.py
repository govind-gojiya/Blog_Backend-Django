from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Tag(models.Model):
    label = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.label


class TaggedItemManager(models.Manager):
    def get_tags_for(self, object_type, object_id):
        contenttype = ContentType.objects.get_for_model(object_type) 
        
        return TaggedItem.objects \
                .select_related('tag') \
                .filter(
                    content_type=contenttype,
                    object_id=object_id
                )

class TaggedItem(models.Model):
    objects = TaggedItemManager()
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()