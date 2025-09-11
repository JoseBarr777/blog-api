from django.contrib import admin

from .models import Post

# Register your models here.

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_at']
    list_filter = ['status', 'author', 'published_at']
    search_fields = ['title', 'body']
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ['created_at', 'updated_at', 'published_at']