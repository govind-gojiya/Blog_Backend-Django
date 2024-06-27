import datetime
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from blog.models import Post

@receiver(pre_save, sender=Post)
def create_timestamp_at_approved(sender, **kwargs):
    instance = kwargs['instance']
    if instance.status == Post.APPROVED:
        instance.approved_at = datetime.datetime.now()
        instance.is_private = 0