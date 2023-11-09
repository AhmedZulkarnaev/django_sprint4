from django.db.models import Count


# Функция для аннотации количества комментариев к постам
def count_comment(queryset):
    return queryset.annotate(comment_count=Count('comments'))
