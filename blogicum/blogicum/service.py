from django.core.paginator import Paginator
from django.utils import timezone

from blog.models import Post
from blogicum.constants import TOTAL_POST


def get_published_posts():
    """Получение опубликованных постов."""
    return Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )


def paginate_page(request, posts, total=TOTAL_POST):
    paginator = Paginator(posts, total)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
