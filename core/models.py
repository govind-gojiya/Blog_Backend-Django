from django.contrib.auth.models import AbstractUser
from django.db import models
from blog.models import TimeStampedModel
from blog.validators import validate_file_size


class Role(models.Model):
    role_id = models.BigAutoField(primary_key=True, unique=True)
    role_name = models.CharField(max_length=100)


class User(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False)
    username = models.CharField(max_length=255, unique=False, null=False, blank=False)
    profile_picture = models.ImageField(upload_to='users/profile_photo', validators=[validate_file_size], null=True, blank=True)
    role = models.ForeignKey(Role, related_name='users', on_delete=models.SET_NULL, null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    liked_posts = models.ManyToManyField(
        'blog.Post',
        related_name='liked_by',
        blank=True
    )

