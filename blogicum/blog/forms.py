from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from blog.constants import FIRST_NAME, LAST__NAME

from .models import Post, Comment, User


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'is_published')
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date'})
        }


class UserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=FIRST_NAME,
        required=True,
        help_text='Имя'
    )
    last_name = forms.CharField(
        max_length=LAST__NAME,
        required=True,
        help_text='Фамилия'
    )

    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name')


class UserProfileEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)


class CommentDeleteForm(forms.Form):
    pass
