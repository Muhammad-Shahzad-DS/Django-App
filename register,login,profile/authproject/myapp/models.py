from django.db import models
from django.contrib.auth.models import AbstractUser

class AuthUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)

    #Email should be unique (this is okay to override)
    email = models.EmailField(unique=True)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)



