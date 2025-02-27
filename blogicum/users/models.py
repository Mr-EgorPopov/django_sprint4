from django.contrib.auth.models import AbstractUser


class MyUser(AbstractUser):
    pass

    def __str__(self):
        return self.username
