



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

    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
# models.py
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    


    

class Disease(models.Model):
    item_photo = models.ImageField(upload_to='photos',blank=True, null=True)
    disease_name = models.CharField(max_length=255,blank=True, null=True)
    disease_symptom = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.disease_name or "Unnamed Disease"

class Supplier(models.Model):
    supplier_name = models.CharField(max_length=255, blank=True, null= True)
    company = models.CharField(max_length=255, blank=True, null= True)
    contact_person = models.CharField(max_length=255, blank= True, null= True)
    email = models.EmailField(blank=True, null= True)
    phone = models.CharField(blank=True,null= True)
    address = models.TextField(blank=True, null= True)
    status = models.BooleanField(blank=True, null= True)
    def __str__(self):
        return self.supplier_name or "Unnamed Supplier"
    

class Item(models.Model):
    category = models.ForeignKey(Category, on_delete= models.CASCADE)

    item_photo = models.ImageField(upload_to='photos')
    disease = models.ForeignKey(Disease, on_delete= models.CASCADE, blank=True, null=True)
    primary_supplier = models.ForeignKey(Supplier, on_delete= models.CASCADE, blank=True, null=True)
    strength = models.CharField(max_length=50, blank=True, null=True)
    item_name = models.CharField(max_length=255)
    item_quantity =models.PositiveIntegerField()
    item_price = models.PositiveIntegerField()
    purcharse_price = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0, blank= True, null= True)
    item_description = models.TextField()
    exp_date = models.DateField()
    brand_name = models.CharField(max_length=255, blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    
    stock_minimum = models.PositiveIntegerField(default=10)
    is_limited = models.BooleanField(default=False)
    max_quantity = models.PositiveIntegerField(default=5)
    last_ordered = models.DateField(blank=True, null=True)
    def __str__(self):
        return self.item_name
    

class PurchaseOrder(models.Model):
    item = models.ForeignKey( Item, on_delete=models.CASCADE, blank=True,null=True)

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, blank=True,null=True)
    po_number = models.CharField(max_length=50, blank=True,null=True, unique= True)
    order_date = models.DateField( blank=True,null=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], blank=True,null=True)
    notes = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True,null=True)
    total_cost = models.PositiveIntegerField(blank=True, null= True)
    created_date = models.DateTimeField(auto_now_add= True, blank=True, null= True)
    def __str__(self):
        return f"{self.supplier} - {self.po_number}"

class PurchaseItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items', blank=True,null=True)
    item = models.ForeignKey( Item, on_delete=models.CASCADE, blank=True,null=True)
    batch_number = models.CharField(max_length=100, blank=True,null=True)
    quantity = models.IntegerField( blank=True,null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True,null=True)

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.item} x {self.quantity}"
    
   


    

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')  # 🆕
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    total_amount = models.PositiveIntegerField(default=0)
    created_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, blank=True, null=True)
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
        return f"CartProduct: {self.item} (Qty: {self.qty})"
    

class Sale(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    invoice_no = models.CharField(max_length=100)
    total_amount = models.PositiveIntegerField()
    created_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Invoice {self.invoice_no} - {self.total_amount}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    def __str__(self):
        return f"{self.item.item_name if self.item else 'Unknown Item'} - {self.quantity} pcs"

class StockHistory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, blank=True, null=True)

    action = models.CharField(choices=[('in', 'In'), ('out', 'Out')])
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.item.item_name}  - {self.quantity}"
    

class Possalesreport(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()

    amount = models.PositiveIntegerField()
    created_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.item

class customerpos(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null= True)
    def __str__(self):
        return self.name