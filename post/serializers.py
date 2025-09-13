from rest_framework import serializers
from django.urls import reverse

from .models import Post

class PostListSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['title', 'published_at', 'url']
        
    def get_url(self, obj):
        try:
            return reverse('post-detail', kwargs={'slug': obj.slug})
        except:
            return f"/api/v1/posts/{obj.slug}/"  # Fallback
    
class PostDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'slug', 'body', 'author', 'published_at', 'created_at', 'updated_at']