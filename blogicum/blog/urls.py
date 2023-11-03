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
    path('<int:pk>/edit/', views.PostUpdateView.as_view(), name='edit_post'),
    path(
        '<int:pk>/delete/',
        views.PostDeleteView.as_view(),
        name='delete_post'
    ),
    path(
        "category/<slug:category_slug>/",
        views.category_posts,
        name="category_posts"
    ),
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    path(
        'comment/<int:comment_id>/edit/',
        views.edit_comment,
        name='edit_comment'
    ),
    path(
        'comment/<int:comment_id>/delete/',
        views.delete_comment,
        name='delete_comment'
    ),
    path('profile/<str:username>/', views.user_profile, name='profile'),
    path(
        'profile/<str:username>/edit/',
        views.edit_profile,
        name='edit_profile'
    ),
]
