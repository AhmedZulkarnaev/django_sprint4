from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DetailView, ListView
)
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.db.models import Count, Q
from django.db.models.functions import Now
from django.http import Http404


from .models import Category, Post, User, Comment
from .constants import POSTS_LIMIT
from .forms import PostForm, CommentForm, UserProfileEditForm, UserCreationForm


# Функция для аннотации количества комментариев к постам
def count_comment(queryset):
    return queryset.annotate(comment_count=Count('comments'))


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
        queryset = super().get_queryset()
        queryset = count_comment(queryset)
        return queryset


# Класс для отображения деталей поста
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post = get_object_or_404(
            Post.objects.select_related('category'),
            pk=self.kwargs['post_id']
        )
        if post.is_published or (self.request.user == post.author):
            return post
        else:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


# Миксин для проверки доступа при редактировании и удалении поста
class DispatchMixin:
    def dispatch(self, request, *args, **kwargs):
        self.post_id = kwargs['pk']
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', post_id=self.post_id)
        return super().dispatch(request, *args, **kwargs)


@login_required
def post_update_view(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    # Проверка, является ли текущий пользователь автором поста
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.instance.is_published = True
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)

    context = {
        'form': form,
        'post': post,
    }

    return render(request, 'blog/create.html', context)


# Класс для удаления поста
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')


# Класс для создания поста
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        delayed_date = form.cleaned_data.get('pub_date')

        if delayed_date and delayed_date > timezone.now():
            form.instance.is_published = False
            return super().form_valid(form)
        else:
            form.instance.is_published = True
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
    category = get_object_or_404(Category, slug=category_slug)

    # Проверка, опубликована ли категория
    if not category.is_published:
        raise Http404

    posts = get_published_posts().filter(
        Q(category=category, author=request.user) | Q(category=category)
    ).order_by('-pub_date')

    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }

    return render(request, template_name, context)


# Функция для добавления комментария
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


# Функция для редактирования комментария
@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=comment.post.pk)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/create.html', {'form': form})


# Класс для регистрации пользователей
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


def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.select_related('category', 'author', 'location')

    if user == request.user:
        posts = posts.order_by('-pub_date')
    elif request.user.is_staff:
        posts = posts.order_by('-pub_date')
    else:
        posts = get_published_posts(posts)

    posts = count_comment(posts).order_by('-pub_date')
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


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
