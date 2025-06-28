



# models.py
from django.contrib.auth.models import User
from django.db import models

from django.utils import timezone

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('pharmacist', 'Pharmacist'),
        ('customer', 'Customer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def str(self):
        return f"{self.user.username} ({self.role})"
    
# models.py
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
   
class Item(models.Model):
    category = models.ForeignKey(Category, on_delete= models.CASCADE)

    item_photo = models.ImageField(upload_to='photos')

    
    item_name = models.CharField(max_length=255)
    item_quantity =models.PositiveIntegerField()
    item_price = models.PositiveIntegerField()
    purcharse_price = models.PositiveIntegerField(default=0)
    item_description = models.TextField()
    exp_date = models.DateField()
    brand_name = models.CharField(max_length=255, blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    stock_minimum = models.PositiveIntegerField(default=10)
    is_limited = models.BooleanField(default=False)
    max_quantity = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.item_name
    

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')  # 🆕
    total_amount = models.PositiveIntegerField(default=0)
    created_date = models.DateField(default=timezone.now)

    def update_total_amount(self):
        total = sum([cp.qty * cp.item.item_price for cp in self.cartproduct_set.all()])
        self.total_amount = total
        self.save()
    
class CartProduct(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE)
    item = models.ForeignKey(Item,on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=0)
    price = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.item