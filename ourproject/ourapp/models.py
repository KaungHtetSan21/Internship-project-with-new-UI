
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator



class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', _('Admin')),
        ('pharmacist', _('Pharmacist')),
        ('customer', _('Customer')),
    )

    GENDER_CHOICES = (
        ('male', _('Male')),
        ('female', _('Female')),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    phone = models.CharField(
        max_length=11,
        blank=False,
        null=False,
        validators=[
            RegexValidator(
                regex=r'^\d{11}$',
                message="Phone number must be exactly 11 digits and contain only numbers."
            )
        ],
    )
    # email = models.EmailField( blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))

    def __str__(self):
        return self.name


class Supplier(models.Model):
    supplier_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Supplier Name"))
    company = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Company"))
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Contact Person"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
    phone = models.CharField(
        max_length=11,
        blank=False,
        null=False,
        verbose_name=_("Phone"),
        validators=[
            RegexValidator(
                regex=r'^\d{11}$',
                message=_("Phone number must be exactly 11 digits (numbers only).")
            )
        ],
    )    
    address = models.TextField(blank=True, null=True, verbose_name=_("Address"))
    status = models.BooleanField(blank=True, null=True, verbose_name=_("Active"))

    def __str__(self):
        return self.supplier_name or _("Unnamed Supplier")


class Item(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("Category"))
    item_photo = models.ImageField(upload_to='photos', verbose_name=_("Photo"))
    primary_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_("Primary Supplier"))
    strength = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Strength"))
    item_name = models.CharField(max_length=255, verbose_name=_("Item Name"))
    item_quantity = models.PositiveIntegerField(verbose_name=_("Quantity"))
    item_price = models.PositiveIntegerField(verbose_name=_("Selling Price"))
    purcharse_price = models.PositiveIntegerField(default=0, verbose_name=_("Purchase Price"))
    reorder_level = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name=_("Reorder Level"))
    item_description = models.TextField(verbose_name=_("Description"))
    exp_date = models.DateField(verbose_name=_("Expiry Date"))
    brand_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Brand Name"))
    batch_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Batch Number"))
    stock_minimum = models.PositiveIntegerField(default=10, verbose_name=_("Minimum Stock"))
    is_limited = models.BooleanField(default=False, verbose_name=_("Limited Stock"))
    max_quantity = models.PositiveIntegerField(default=5, verbose_name=_("Maximum Quantity"))
    last_ordered = models.DateField(blank=True, null=True, verbose_name=_("Last Ordered"))

    def __str__(self):
        return self.item_name


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', _('Pending')),
        ('Completed', _('Completed')),
        ('Cancelled', _('Cancelled')),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_("Item"))

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_("Supplier"))
    po_number = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name=_("PO Number"))
    order_date = models.DateField(blank=True, null=True, verbose_name=_("Order Date"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True, verbose_name=_("Status"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True, verbose_name=_("Total Amount"))
    total_cost = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Total Cost"))
    created_date = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=_("Created Date"))

    def __str__(self):
        return f"{self.supplier} - {self.po_number}"


class PurchaseItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items', blank=True, null=True, verbose_name=_("Order"))
    item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_("Item"))
    batch_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Batch Number"))
    quantity = models.IntegerField(blank=True, null=True, verbose_name=_("Quantity"))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name=_("Unit Price"))

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.item} x {self.quantity}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', verbose_name=_("User"))
    customer_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Customer Name"))
    total_amount = models.PositiveIntegerField(default=0, verbose_name=_("Total Amount"))
    created_date = models.DateTimeField(default=timezone.now, verbose_name=_("Created Date"))
    payment_method = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Payment Method"))
    source = models.CharField(
        max_length=10,
        choices=[('pos', _('POS')), ('online', _('Online'))],
        default='online',
        verbose_name=_("Source")
    )

    def update_total_amount(self):
        total = sum([cp.qty * cp.item.item_price for cp in self.cartproduct_set.all()])
        self.total_amount = total
        self.save()


class CartProduct(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name=_("Cart"))
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"))
    qty = models.PositiveIntegerField(default=0, verbose_name=_("Quantity"))
    price = models.PositiveIntegerField(default=0, verbose_name=_("Price"))

    def __str__(self):
        return f"CartProduct: {self.item} (Qty: {self.qty})"


class Sale(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('cancelled', _('Cancelled')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    invoice_no = models.CharField(max_length=100, verbose_name=_("Invoice No"))
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Customer Name"))
    phone = models.CharField(
        max_length=11,
        blank=False,
        null=False,
        verbose_name=_("Phone"),
        validators=[
            RegexValidator(
                regex=r'^\d{11}$',
                message=_("Phone number must be exactly 11 digits (numbers only).")
            )
        ],
    )    
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Address"))
    total_amount = models.PositiveIntegerField(verbose_name=_("Total Amount"))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Created Date"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', blank=True, null=True, verbose_name=_("Status"))
    final_amount = models.PositiveIntegerField(default=0, verbose_name=_("Final Amount (with tax + shipping)"),blank=True,null=True)
    def __str__(self):
        return f"Invoice {self.invoice_no} - {self.total_amount}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name=_("Sale"))
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"))
    quantity = models.PositiveIntegerField(verbose_name=_("Quantity"))
    price = models.PositiveIntegerField(verbose_name=_("Price"))

    def __str__(self):
        return f"{self.item.item_name if self.item else _('Unknown Item')} - {self.quantity} pcs"


class StockHistory(models.Model):
    ACTION_CHOICES = [
        ('in', _('In')),
        ('out', _('Out')),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"))
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_("Supplier"))
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name=_("Action"))
    quantity = models.PositiveIntegerField(verbose_name=_("Quantity"))
    note = models.TextField(blank=True, null=True, verbose_name=_("Note"))
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))

    def __str__(self):
        return f"{self.item.item_name}  - {self.quantity}"


class Possalesreport(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    quantity = models.PositiveIntegerField(verbose_name=_("Quantity"))
    price = models.PositiveIntegerField(verbose_name=_("Price"))
    amount = models.PositiveIntegerField(verbose_name=_("Amount"))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Created Date"))

    def __str__(self):
        return str(self.item)


class customerpos(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Customer Name"))
    phone = models.CharField(
        max_length=11,
        blank=False,
        null=False,
        verbose_name=_("Phone"),
        validators=[
            RegexValidator(
                regex=r'^\d{11}$',
                message=_("Phone number must be exactly 11 digits (numbers only).")
            )
        ],
    )    
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Address"))

    def __str__(self):
        return self.name


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True, verbose_name=_("Recipient"))
    message = models.TextField(blank=True, null=True, verbose_name=_("Message"))
    is_read = models.BooleanField(default=False, blank=True, null=True, verbose_name=_("Read"))
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=_("Created At"))

    def __str__(self):
        return f"To: {self.recipient.username} | {self.message[:1000]}"


class Chatbot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_("User"))
    questions = models.TextField(blank=True, null=True, verbose_name=_("Questions"))
    answers = models.TextField(blank=True, null=True, verbose_name=_("Answers"))
    timeline = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=_("Timestamp"))

######## Create OTP Model
import random
from django.utils import timezone
from datetime import timedelta

class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)