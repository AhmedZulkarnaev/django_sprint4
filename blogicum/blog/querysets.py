from django.db.models import Count
from django.core.paginator import Paginator
from django.db.models.functions import Now

from .models import Post
# from .constants import POSTS_LIMIT


# Функция для аннотации количества комментариев к постам
def count_comment(queryset):
    return queryset.annotate(comment_count=Count('comments')).order_by(
        '-pub_date'
    )


# Функция для пагинации постов
def paginate_posts(page_number, posts, limit):
    paginator = Paginator(posts, limit)
    page_obj = paginator.get_page(page_number)

    return page_obj


# Функция для получения опубликованных постов
def get_published_posts(manager=Post.objects):
    return (
        manager.filter(
            pub_date__lte=Now(),
            is_published=True,
            category__is_published=True,
        )
        .select_related('category', 'author', 'location')
        .order_by('-pub_date')
    )
