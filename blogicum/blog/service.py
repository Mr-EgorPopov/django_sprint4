from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count

from blog.models import Post
from blogicum.constants import TOTAL_POST


def get_published_posts(
        author=False,
        comment_count=False,
        three_category=False,
        profile=False,
):
    """Получение опубликованных постов."""
    queryset_flash = Post.objects.select_related(
        'category',
        'author',
        'location',
    )
    queryset = Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )
    if author:
        queryset = queryset.select_related('author')
    elif comment_count:
        queryset = queryset.select_related('author').annotate(
            comment_count=Count('comments')).order_by('-pub_date')
    elif three_category:
        queryset = queryset.select_related(
            'category',
            'author',
            'location'
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    elif profile:
        queryset = queryset_flash.annotate(comment_count=Count(
            'comments'
        )).order_by('-pub_date')
    return queryset


def paginate_page(request, posts, total=TOTAL_POST):
    paginator = Paginator(posts, total)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
