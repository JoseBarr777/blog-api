from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from markdownx.models import MarkdownxField

class PostStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    ARCHIVED = 'archived', 'Archived'

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    # body = models.TextField()
    body = MarkdownxField()  # stores raw Markdown; editor handles preview/uploads
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
            max_length=20,
            choices=PostStatus.choices,
            default=PostStatus.DRAFT
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.status == PostStatus.PUBLISHED:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)