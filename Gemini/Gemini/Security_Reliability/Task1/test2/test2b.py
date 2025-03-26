from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string

class User(AbstractUser):
    # Add any custom fields here
    password_reset_token = models.CharField(max_length=128, null=True, blank=True)

    def generate_password_reset_token(self):
        self.password_reset_token = get_random_string(length=32)
        self.save()

# In your views:
def register(request):
    # ...
    user = User.objects.create_user(username=username, email=email, password=password)
    # ...

def login(request):
    # ...
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
    # ...