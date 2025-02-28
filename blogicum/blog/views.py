from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy, reverse

from django.views.generic import CreateView, UpdateView, ListView
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count

from blog.models import Post, Category, Comment
from blog.forms import PostForm, CommentForm, ProfileForm
from blogicum.constants import TOTAL_POST
from blogicum.service import get_published_posts, paginate_page


User = get_user_model()


def index(request):
    """Отображение постов на главной странице."""
    template = 'blog/index.html'
    posts = get_published_posts().annotate(
        comment_count=Count('comments')).order_by('-pub_date')
    context = {'page_obj': paginate_page(request, posts)}
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница с полной публикацией из блога."""
    if request.user.is_authenticated:
        post = get_object_or_404(
            Post.objects.filter(
                pk=post_id,
                author=request.user
            ) | get_published_posts().filter(pk=post_id)
        )
    else:
        post = get_object_or_404(
            get_published_posts(),
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
        current_time = timezone.now()
        return Post.objects.select_related(
            'category',
            'author',
            'location'
        ).filter(
            pub_date__lte=current_time,
            is_published=True,
            category=category,
            category__is_published=True,
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')

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
    if request.user == user:
        posts = Post.objects.select_related(
            'category', 'author', 'location',
        ).annotate(comment_count=Count(
            'comments'
        )).order_by('-pub_date').filter(
            author=user.id
        )
    else:
        posts = Post.objects.select_related(
            'category', 'author', 'location',
        ).annotate(comment_count=Count(
            'comments'
        )).order_by('-pub_date').filter(
            author=user,
            is_published=True,
            pub_date__lte=timezone.now()
        )
    template = 'blog/profile.html'
    context = {
        'profile': user,
        'page_obj': paginate_page(request, posts),
    }
    return render(request, template, context)


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
    template_name = 'blog/create.html'
    post = get_object_or_404(
        Post, pk=post_id, author__username=request.user
    )
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    context = {
        'post': post,
    }
    return render(request, template_name, context)


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
    template = 'blog/comment.html'
    context = {
        'form': form,
        'post': post,
        'comment': comment,
    }
    return render(request, template, context)


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
    template = 'blog/comment.html'
    context = {
        'post': post,
        'comment': comment,
    }
    return render(request, template, context)


@login_required
def edit_profile(request):
    """Редактирование профиля."""
    template = 'blog/user.html'
    instance = request.user
    form = ProfileForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect(
            'blog:profile',
            username=instance.username
        )
    context = {'form': form}
    return render(request, template, context)
