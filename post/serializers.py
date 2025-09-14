from rest_framework import serializers
from django.urls import reverse
import nh3
from markdownx.utils import markdownify

from .models import Post

class PostListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='post:post-detail',
        lookup_field='slug'
    )
    
    class Meta:
        model = Post
        fields = ['title', 'published_at', 'url']

 
class PostDetailSerializer(serializers.ModelSerializer):
    body = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    
    def get_body(self, obj):
        try:
            html = markdownify(obj.body)
            clean_html = nh3.clean(
                html,
                tags={'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre'},
                attributes={'a': {'href', 'title'}},
            )
            return clean_html
        except Exception:
            return obj.body  # Fallback to raw markdown if processing fails
    
    def get_author(self, obj):
        # return author name instead of ID
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.username
    
    class Meta:
        model = Post
        fields = ['title', 'slug', 'body', 'author', 'published_at', 'created_at', 'updated_at']