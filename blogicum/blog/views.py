from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import (
    CreateView,
    UpdateView,
    ListView
)
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


from .models import Post, Category, Comment
from blog.forms import PostForm, CommentForm, ProfileForm
from blogicum.constants import TOTAL_POST

User = get_user_model()


def get_published_posts():
    """Получение опубликованных постов"""
    return Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )


def index(request):
    """Отображение постов на главной странице"""
    template = 'blog/index.html'
    current_time = timezone.now()
    post = Post.objects.select_related('category').filter(
        pub_date__lte=current_time,
        is_published=True,
        category__is_published=True,
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    paginator = Paginator(post, TOTAL_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница с полной публикацией из блога"""
    if request.user.is_authenticated:
        post = get_object_or_404(
            Post.objects.filter(
                pk=post_id,
                author=request.user
            ) | Post.objects.filter(
                pk=post_id,
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            )
        )
    else:
        post = get_object_or_404(
            get_published_posts(),
            pk=post_id
        )

    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm()

    comments = post.comments.all()
    context = {
        'form': form,
        'post': post,
        'comments': comments
    }
    return render(request, 'blog/detail.html', context)


class CategoryPostsView(ListView):
    """Отображение постов в категории"""

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
    """Создание поста"""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog/profile.html')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={
                'username': self.object.author.username
            }
        )


def profile(request, username):
    """Профиль пользователя."""
    user = get_object_or_404(User, username=username)
    post = Post.objects.select_related(
        'category', 'author', 'location',
    ).annotate(comment_count=Count('comments')).order_by('-pub_date').filter(
        author=user.id
    )
    paginator = Paginator(post, TOTAL_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'blog/profile.html'
    context = {
        'profile': user,
        'page_obj': page_obj,
        'post': post,
    }
    return render(request, template, context)


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментария"""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    context_object_name = 'comment'
    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование поста"""
    
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk}
        )

    def handle_no_permission(self):
        post_id = self.kwargs['post_id']
        return redirect('blog:post_detail', post_id=post_id)


@login_required
def delete_post(request, post_id):
    """Удаление поста"""
    template_name = 'blog/create.html'
    post = get_object_or_404(
        Post, pk=post_id, author__username=request.user
    )
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    context = {
        'post': post,
        'is_delete': True,
    }
    return render(request, template_name, context)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария"""
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
        return redirect('blog:post_detail', post_id)
    else:
        form = CommentForm(instance=comment)
    return render(
        request,
        'blog/comment.html',
        {
            'form': form,
            'post': post,
            'comment': comment
        }
    )


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария"""
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, id=comment_id, post=post)

    if request.user != comment.author:
        raise PermissionDenied("Вы не можете редактировать этот комментарий.")
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id)
    return render(
        request,
        'blog/comment.html',
        {
            'post': post,
            'comment': comment
        }
    )


@login_required
def edit_profile(request):
    """Редактирование профиля"""
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
