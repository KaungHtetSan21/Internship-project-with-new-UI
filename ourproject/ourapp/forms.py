# forms.py
from django import forms
from django.contrib.auth.models import User
from .models import *

class CustomerRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    # ✅ UserProfile fields
    phone = forms.CharField(max_length=20, required=True)
    address = forms.CharField(max_length=255, required=False)
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')], required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password != confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
    


# class SupplierForm(forms.ModelForm):
#     class Meta:
#         model = Supplier
#         fields = ['supplier_name', 'supplier_phnumber', 'supplier_location']

# class PurchaseOrderForm(forms.ModelForm):
#     class Meta:
#         model = PurchaseOrder
#         fields = ['supplier', 'po_number', 'order_date', 'status', 'notes']

# class PurchaseItemForm(forms.ModelForm):
#     class Meta:
#         model = PurchaseItem
#         fields = ['medicine_name', 'batch_number', 'quantity', 'unit_price']