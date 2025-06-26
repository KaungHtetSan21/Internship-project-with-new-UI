



# models.py
from django.contrib.auth.models import User
from django.db import models

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('pharmacist', 'Pharmacist'),
        ('customer', 'Customer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    def str(self):
        return f"{self.user.username} ({self.role})"