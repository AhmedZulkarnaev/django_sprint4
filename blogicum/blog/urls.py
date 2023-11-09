from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.PostListView.as_view(), name="index"),
    path(
        "posts/<int:post_id>/",
        views.PostDetailView.as_view(),
        name="post_detail"
    ),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    path(
        'posts/<int:post_id>/edit/',
        views.post_update_view,
        name='edit_post'
    ),
    path(
        'posts/<int:post_id>/delete/',
        views.delete_post,
        name='delete_post'
    ),
    path(
        "category/<slug:category_slug>/",
        views.category_posts,
        name="category_posts"
    ),
    path(
        'posts/<int:post_id>/<int:comment/',
        views.CommentCreateView.as_view(),
        name='add_comment'
    ),
    path(
        'posts/<int:post_id>/edit/<int:pk>/',
        views.CommentUpdateView.as_view(),
        name='edit_comment'
    ),
    path(
        'posts/<int:post_id>/delete_comment/<int:comment_id>/',
        views.CommentDeleteView.as_view(),
        name='delete_comment'
    ),

    path('profile/<str:username>/', views.user_profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile')
]
