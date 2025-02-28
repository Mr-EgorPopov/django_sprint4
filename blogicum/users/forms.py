from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import MyUser

user = get_user_model()


class ConsumerCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = MyUser
