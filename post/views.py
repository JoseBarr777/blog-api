from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, IsoDateTimeFilter

from .models import Post, PostStatus
from .serializers import PostListSerializer, PostDetailSerializer


class PostFilter(FilterSet):
    published_after = IsoDateTimeFilter(
        field_name="published_at",
        lookup_expr="gte",
        label="Published at ≥ (ISO 8601, e.g. 2025-09-12T10:00:00Z)",
    )
    published_before = IsoDateTimeFilter(
        field_name="published_at",
        lookup_expr="lte",
        label="Published at ≤ (ISO 8601, e.g. 2025-09-13T18:00:00Z)",
    )

    class Meta:
        model = Post
        fields = []


class PostListView(generics.ListAPIView):
    """
    List posts.

    Query params:
      - search: Case-insensitive match on title, body, author first/last name.
      - published_after: ISO 8601 datetime; includes items with published_at >= value.
      - published_before: ISO 8601 datetime; includes items with published_at <= value.
      - ordering: published_at, -published_at, created_at, -created_at (default: -published_at).

    Notes:
      - Results are paginated per DRF settings (e.g., PAGE_SIZE).
    """

    serializer_class = PostListSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["title", "body", "author__first_name", "author__last_name"]
    filterset_class = PostFilter
    ordering_fields = ["published_at", "created_at"]
    ordering = ["-published_at", "-id"]

    def get_queryset(self):
        # Published-only list; optimized for author data in the list serializer
        return (
            Post.objects.filter(status=PostStatus.PUBLISHED)
            .select_related("author")
        )

class PostDetailView(generics.RetrieveAPIView):
    """
    Retrieve a single post by slug.
    
    Returns 404 for non-existent or unpublished posts.
    Converts markdown body to sanitized HTML.
    """
    
    serializer_class = PostDetailSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        # Only published posts, with author data
        return (
            Post.objects.filter(status=PostStatus.PUBLISHED)
            .select_related("author")
        )