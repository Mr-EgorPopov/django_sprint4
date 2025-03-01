from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone

from blog.models import Post
from blogicum.constants import TOTAL_POST


def get_published_posts(
        comment_count=True,
        on_filter=True
):
    """Получение опубликованных постов."""
    queryset_flash = Post.objects.select_related(
        'category',
        'author',
        'location',
    )
    if comment_count:
        queryset_flash = queryset_flash.annotate(
            comment_count=Count('comments')).order_by('-pub_date')
    if on_filter:
        queryset_flash = queryset_flash.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
    return queryset_flash


def paginate_page(request, posts, total=TOTAL_POST):
    paginator = Paginator(posts, total)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
