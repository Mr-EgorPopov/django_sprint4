from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import MyUser


user = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = MyUser