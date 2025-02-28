from django.urls import include, path, reverse_lazy

from blog import views

app_name = 'blog'

posts_urls = [
    path(
        '<int:post_id>/comment/',
        views.CommentCreateView.as_view(),
        # views.add_comment,
        name='add_comment'
    ),
    path(
        'create/',
        views.PostCreateView.as_view(
            success_url=reverse_lazy('blog:profile'),
        ),
        name='create_post',
    ),
    path(
        '<int:post_id>/edit/',
        views.PostUpdateView.as_view(),
        name='edit_post'
    ),
    path(
        '<int:post_id>/delete/',
        views.delete_post,
        name='delete_post'
    ),
    path(
        '<int:post_id>/edit_comment/<int:comment_id>/',
        views.edit_comment,
        name='edit_comment'
    ),
    path(
        '<int:post_id>/edit_comment/<int:comment_id>/',
        views.edit_comment,
        name='edit_comment'
    ),
    path(
        '<int:post_id>/delete_comment/<int:comment_id>/',
        views.delete_comment,
        name='delete_comment'
    ),
    path(
        '<int:post_id>/',
        views.post_detail,
        name='post_detail'
    ),
]

urlpatterns = [
    path(
        'posts/',
        include(posts_urls)
    ),
    path(
        'category/<slug:category_slug>/',
        views.CategoryPostsView.as_view(),
        name='category_posts'
    ),
    path(
        '',
        views.index,
        name='index'
    ),
    path(
        'profile/<str:username>/',
        views.profile,
        name='profile'
    ),
    path(
        'edit_profile/',
        views.edit_profile,
        name='edit_profile'
    ),
]
