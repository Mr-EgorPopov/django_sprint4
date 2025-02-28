from django.contrib.auth.models import AbstractUser


class Subscriber(AbstractUser):
    pass

    def __str__(self):
        return self.username
