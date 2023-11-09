from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DetailView, ListView, UpdateView, DeleteView
)
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.db.models import Q, Count
from django.db.models.functions import Now
from django.http import Http404


from .models import Category, Post, User, Comment
from .constants import POSTS_LIMIT
from .forms import PostForm, CommentForm, UserProfileEditForm, UserCreationForm
from .querysets import count_comment


# Функция для пагинации постов
def paginate_posts(request, posts, limit):
    paginator = Paginator(posts, limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj


# Функция для получения опубликованных постов
def get_published_posts(manager=Post.objects):
    return manager.filter(
        pub_date__lte=Now(),
        is_published=True,
        category__is_published=True,
    )


# Класс для отображения списка постов
class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = get_published_posts().select_related('category')
    ordering = '-pub_date'
    paginate_by = POSTS_LIMIT

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_published=True)
        queryset = queryset.select_related('category', 'author', 'location')
        queryset = self.count_comment(queryset)
        return queryset

    def count_comment(self, queryset):
        return queryset.annotate(comment_count=Count('comments'))


# Класс для отображения деталей поста
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post = get_object_or_404(
            Post.objects.select_related('category'),
            pk=self.kwargs['post_id']
        )

        if (
            not post.is_published
                or not post.category.is_published
                or post.pub_date > timezone.now()
        ) and post.author != self.request.user:
            raise Http404("Page not published")
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments
            .select_related('author')
            .order_by('created_at')
        )
        return context


# Миксин для проверки доступа при редактировании и удалении поста
class DispatchMixin:
    def dispatch(self, request, *args, **kwargs):
        self.post_id = kwargs['pk']
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', post_id=self.post_id)
        return super().dispatch(request, *args, **kwargs)


# Фукнция для изменения поста
@login_required
def post_update_view(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)

    form = PostForm(request.POST, request.FILES, instance=post)
    if form.is_valid():
        form.instance.is_published
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)

    context = {
        'form': form,
        'post': post,
    }

    return render(request, 'blog/create.html', context)


# Функция для удаления поста
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html', {'post': post})


# Класс для создания поста
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        if form.instance.pub_date <= timezone.now():
            form.instance.is_published = True
        else:
            form.instance.is_published = False
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=(
                self.request.user.get_username(),
            )
        )


# Функция для отображения постов в категории
def category_posts(request, category_slug):
    template_name = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    posts = get_published_posts().select_related('category').filter(
        Q(category=category, author=request.user) | Q(category=category)
    ).order_by('-pub_date')

    page_obj = paginate_posts(request, posts, POSTS_LIMIT)

    context = {
        'category': category,
        'page_obj': page_obj,
    }

    return render(request, template_name, context)


# Класс для регистрации пользователя
class UserRegistrationView(CreateView):
    template_name = 'registration/registration_form.html'
    form_class = UserCreationForm
    model = User
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


# Класс для входа пользователей
class LoginView(LoginView):
    def get_success_url(self):
        username = self.request.user.get_username()
        return reverse('blog:profile', args=[username])


# Функция для профиля пользователя
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.select_related('category', 'author', 'location')

    if user == request.user:
        posts = posts.order_by('-pub_date')
    else:
        posts = get_published_posts(posts)

    page_obj = paginate_posts(request, posts, POSTS_LIMIT)

    posts = count_comment(posts).order_by('-pub_date')
    page_obj = paginate_posts(request, posts, POSTS_LIMIT)
    context = {
        'profile': user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


# Функция для изменения профиля пользователя
@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=user.username)
    else:
        form = UserProfileEditForm(instance=user)

    return render(request, 'blog/create.html', {'form': form})


# Класс для создания комментария
class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.save()
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


# Миксин с общими полями
class CommentMixin(LoginRequiredMixin):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)

    def get_success_url(self):
        post_id = self.object.post.pk
        return reverse('blog:post_detail', kwargs={'post_id': post_id})


# Класс для изменения комментария
class CommentUpdateView(CommentMixin, UpdateView):
    pass


# Класс для удаления комментария
class CommentDeleteView(CommentMixin, DeleteView):
    pk_url_kwarg = "comment_id"
