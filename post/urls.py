from django.urls import path

from . import views

app_name = "post"

urlpatterns = [
    path("posts/", views.PostListView.as_view(), name="post-list"),
    # path("posts/<str:slug>/", views.PostDetailsView.as_view(), name="post-details"),
]
