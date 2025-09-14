from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from .models import Post

# Register your models here.

# @admin.register(Post)
# class PostAdmin(admin.ModelAdmin):
#     list_display = ['title', 'author', 'status', 'published_at']
#     list_filter = ['status', 'author', 'published_at']
#     search_fields = ['title', 'body']
#     prepopulated_fields = {"slug": ("title",)}
#     readonly_fields = ['created_at', 'updated_at', 'published_at']

@admin.register(Post)
class PostAdmin(MarkdownxModelAdmin):
    list_display = ['title', 'author', 'status', 'published_at']
    list_filter = ['status', 'author', 'published_at']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'published_at']

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'body', 'author', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )