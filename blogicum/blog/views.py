from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView

from blog.forms import CommentForm, PostForm, ProfileForm
from blog.models import Category, Comment, Post
from blog.service import get_published_posts, paginate_page
from blogicum.constants import TOTAL_POST

User = get_user_model()


def index(request):
    """Отображение постов на главной странице."""
    posts = get_published_posts()
    context = {'page_obj': paginate_page(request, posts)}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    """Страница с полной публикацией из блога."""
    if request.user.is_authenticated:
        post = get_object_or_404(
            Post.objects.filter(
                pk=post_id,
                author=request.user
            ) | get_published_posts(
                comment_count=False,
            ).filter(pk=post_id)
        )
    else:
        post = get_object_or_404(
            get_published_posts(
                comment_count=False,
            ),
            pk=post_id
        )
    form = CommentForm()
    comments = post.comments.select_related('author').all()
    context = {
        'form': form,
        'post': post,
        'comments': comments
    }
    return render(request, 'blog/detail.html', context)


class CategoryPostsView(ListView):
    """Отображение постов в категории."""

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'posts'
    paginate_by = TOTAL_POST

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        return get_published_posts().filter(
            category=category,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug']
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={
                'username': self.object.author.username
            }
        )


def profile(request, username):
    """Профиль пользователя."""
    user = get_object_or_404(User, username=username)
    posts = get_published_posts(
        on_filter=request.user != user
    ).filter(author=user)
    context = {
        'profile': user,
        'page_obj': paginate_page(request, posts),
    }
    return render(request, 'blog/profile.html', context)


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )

    def handle_no_permission(self):
        post_id = self.kwargs['post_id']
        return redirect('blog:post_detail', post_id=post_id)


@login_required
def delete_post(request, post_id):
    """Удаление поста."""
    post = get_object_or_404(
        Post, pk=post_id, author__username=request.user
    )
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    context = {
        'post': post,
    }
    return render(request, 'blog/create.html', context)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария."""
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    context = {
        'form': form,
        'post': post,
        'comment': comment,
    }
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария."""
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == "POST":
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    context = {
        'post': post,
        'comment': comment,
    }
    return render(request, 'blog/comment.html', context)


@login_required
def edit_profile(request):
    """Редактирование профиля."""
    instance = request.user
    form = ProfileForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect(
            'blog:profile',
            username=instance.username
        )
    context = {'form': form}
    return render(request, 'blog/user.html', context)
