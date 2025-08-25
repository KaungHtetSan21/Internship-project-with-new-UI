
# Standard library imports
import json
import datetime
from datetime import date, timedelta

# Django core imports
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views import View
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.dateparse import parse_date

# Django auth imports
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Django ORM utilities
from django.db.models import (
    Sum, Count, Q, F, FloatField, ExpressionWrapper
)
from django.db.models.functions import Coalesce

# Project-specific imports (models, forms)
from .forms import CustomerRegisterForm
from .models import *

# Third-party imports
from google import genai  # if used, otherwise remove
from decimal import Decimal, ROUND_HALF_UP

# 🆕 constants
TAX_RATE = Decimal('0.02')   # 2%
SHIPPING_FEE = 4000

# (optional) utility
def compute_tax(subtotal: int) -> int:
    # kyat အနီးစပ်ဆုံး ရေကွက်တင် (round half up) ၊ int ပြန်
    return int((Decimal(subtotal) * TAX_RATE).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def base(request):
    items = Item.objects.all().order_by('-id')[:4]
    categories = Category.objects.all()
    promotions = PromotionItem.objects.filter(
        status='active',
        quantity__gt=0,
    ).filter(
        models.Q(expire_date__isnull=True) | models.Q(expire_date__gte=timezone.now().date())
    ).order_by('-created_at')[:6]

    context = {
        'items': items,
        'categories': categories,
        'promotions': promotions,
    }
    return render(request, 'base.html', context)

import random
from django.utils import timezone
from django.core.mail import send_mail
from .models import EmailOTP

def customer_register(request):
    # ✅ Already logged in user များကို register ခွင့်မပေးဘူး
    if request.user.is_authenticated:
        try:
            if request.user.userprofile.role == 'customer':
                messages.warning(request, "Customer account ရှိပြီးသား ဖြစ်နေပါတယ်။")
                return redirect('login')
            else:
                messages.error(request, "သင်သည် customer မဟုတ်ပါ။")
                return redirect('login')
        except UserProfile.DoesNotExist:
            pass

    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # ✅ Session ထဲသိမ်း
            request.session['otp_email'] = email
            request.session['reg_data'] = {
                'username': form.cleaned_data['username'],
                'email': email,
                'password': form.cleaned_data['password'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'phone': form.cleaned_data['phone'],
                'address': form.cleaned_data.get('address'),
                'gender': form.cleaned_data.get('gender'),
                'date_of_birth': str(form.cleaned_data.get('date_of_birth')),
                'role': 'customer',
            }

            # ✅ OTP generate
            otp = f"{random.randint(100000, 999999)}"

            # ✅ OTP တည်ဆောက်/ပြင်
            EmailOTP.objects.update_or_create(
                email=email,
                defaults={'otp': otp, 'created_at': timezone.now()}
            )

            # ✅ Email ပေးပို့
            send_mail(
                subject="Your OTP for Pharmacy Registration",
                message=f"Your OTP is: {otp}",
                from_email="khtetsan399@gmail.com",  # ဒီမှာ သင့် email ပြောင်းဖို့လိုတယ်
                recipient_list=[email],
                fail_silently=False,
            )

            messages.info(request, "An OTP has been sent to your email. Please verify.")
            return redirect('verify_registration_otp')  # ✅ make sure you have this URL name

        else:
            messages.error(request, "Form is invalid. Please check your inputs.")
    else:
        form = CustomerRegisterForm()

    return render(request, 'register.html', {'form': form})



from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import EmailOTP, UserProfile
import datetime

def verify_registration_otp(request):
    email = request.session.get('otp_email')
    reg_data = request.session.get('reg_data')

    if not email or not reg_data:
        messages.error(request, "Session expired. Please register again.")
        return redirect('customer_register')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')

        try:
            otp_record = EmailOTP.objects.get(email=email)

            if otp_record.otp == otp_input and not otp_record.is_expired():
                # ✅ Optional Check: avoid duplicate usernames/emails
                if User.objects.filter(username=reg_data['username']).exists():
                    messages.error(request, "Username already taken.")
                    return redirect('customer_register')

                if User.objects.filter(email=reg_data['email']).exists():
                    messages.error(request, "Email already registered.")
                    return redirect('customer_register')

                # ✅ Create user
                user = User.objects.create_user(
                    username=reg_data['username'],
                    email=reg_data['email'],
                    password=reg_data['password'],
                    first_name=reg_data['first_name'],
                    last_name=reg_data['last_name']
                )

                # ✅ Create UserProfile
                UserProfile.objects.create(
                    user=user,
                    role=reg_data['role'],
                    phone=reg_data['phone'],
                    address=reg_data.get('address'),
                    gender=reg_data.get('gender'),
                    date_of_birth=reg_data.get('date_of_birth') or None
                )

                # ✅ Cleanup session + login
                del request.session['otp_email']
                del request.session['reg_data']
                otp_record.delete()

                login(request, user)
                messages.success(request, "Account verified and created successfully.")
                return redirect('customer_dashboard')

            else:
                messages.error(request, "❌ Invalid or expired OTP.")

        except EmailOTP.DoesNotExist:
            messages.error(request, "❌ OTP not found. Please re-register.")
            return redirect('customer_register')

    return render(request, 'verify_registration_otp.html', {
        'email': email
    })


@csrf_exempt
def register_customer_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            name = data.get('username', '').strip()
            phone = data.get('phone')
            address = data.get('address', '')  # optional for now

            # ✅ Check if same name + phone already exists
            if customerpos.objects.filter(name=name, phone=phone).exists():
                return JsonResponse({'error': 'Customer already exists'}, status=400)

            customerpos.objects.create(
                name=name,
                phone=phone,
                address=address
            )

            return JsonResponse({'message': 'Customer registered successfully'})

        except Exception as e:
            return JsonResponse({'error': f'Exception: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

from django.core.mail import send_mail, BadHeaderError
from smtplib import SMTPException
import socket
import random
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import EmailOTP

def forgot_password_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # ✅ Email check
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "This email is not registered.")
            return redirect('forgot_password')

        # ✅ Generate OTP
        otp = f"{random.randint(100000, 999999)}"

        # ✅ Save OTP to DB
        EmailOTP.objects.update_or_create(
            email=email,
            defaults={'otp': otp, 'created_at': timezone.now()}
        )

        # ✅ Save to session
        request.session['reset_email'] = email

        # ✅ Send Email with network error handling
        try:
            send_mail(
                subject="Your OTP for Password Reset",
                message=f"Your OTP is: {otp}",
                from_email="khtetsan399@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "An OTP has been sent to your email.")
            return redirect('verify_reset_otp')

        except (BadHeaderError, SMTPException, socket.error):
            messages.error(request, "⚠ Check your network connection and try again.")
            return redirect('forgot_password')

    # ✅ GET request → Show form
    return render(request, 'auth/forgot_password.html')

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import EmailOTP
from django.utils import timezone

def verify_reset_otp(request):
    email = request.session.get('reset_email')

    if not email:
        messages.error(request, "Session expired. Please start again.")
        return redirect('forgot_password')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')

        try:
            otp_record = EmailOTP.objects.get(email=email)

            if otp_record.otp == otp_input and not otp_record.is_expired():
                # OTP valid => allow password reset
                request.session['otp_verified'] = True
                return redirect('reset_password')

            messages.error(request, "Invalid or expired OTP.")
        except EmailOTP.DoesNotExist:
            messages.error(request, "OTP not found. Please restart the process.")
            return redirect('forgot_password')

    return render(request, 'auth/verify_reset_otp.html', {'email': email})

from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from .forms import SetNewPasswordForm

def set_new_password(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Session expired. Please try again.")
        return redirect('forget_password')  # redirect to step1

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            try:
                user = User.objects.get(email=email)
                user.password = make_password(new_password)
                user.save()

                # ✅ Clean session
                del request.session['reset_email']
                messages.success(request, "Your password has been reset successfully.")
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('forget_password')
    else:
        form = SetNewPasswordForm()

    return render(request, 'auth/set_new_password.html', {'form': form})

from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash

def reset_password_view(request):
    email = request.session.get('reset_email')

    if not email:
        messages.error(request, "Session expired.")
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('reset_password')

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            # optional: keep the user logged in
            update_session_auth_hash(request, user)

            # clear session
            del request.session['reset_email']
            messages.success(request, "Password reset successful.")
            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('forgot_password')

    return render(request, 'reset_password.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                role = user.userprofile.role
            except Exception as e:
                messages.error(request, "UserProfile not found. Please contact admin.")
                return redirect('login')

            login(request, user)

            # ✅ Role-based redirect
            if role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'pharmacist':
                return redirect('pharmacist_dashboard')
            elif role == 'customer':
                return redirect('customer_dashboard')
            else:
                messages.error(request, 'Unknown user role.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')    


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

@login_required
def admin_dashboard(request):
    if request.user.userprofile.role != 'admin':
        return HttpResponseForbidden("Admins only.")
    return render(request, 'admin/dashboard.html')

# @login_required
# def pharmacist_dashboard_view(request):
#     if request.user.userprofile.role != 'pharmacist':
#         return HttpResponseForbidden("Unauthorized")

#     # ✅ POS Orders
#     pos_orders = Cart.objects.filter(payment_method__in=['cash', 'mobile', 'print'])
#     pos_total = pos_orders.count()
#     pos_revenue = pos_orders.aggregate(total=Coalesce(Sum('total_amount'), 0))['total']

#     # ✅ Online Orders (all, for pharmacist to confirm/cancel)
#     online_orders_queryset = (
#         Sale.objects
#         .exclude(user__userprofile__role='pharmacist')
#         .select_related('user')
#         .order_by('-created_date')
#     )

#     paginator = Paginator(online_orders_queryset, 5)
#     page_number = request.GET.get('page')
#     online_orders_list = paginator.get_page(page_number)

#     # ✅ Only confirmed orders counted for totals
#     confirmed_online_orders = online_orders_queryset.filter(status='confirmed')
#     online_total = confirmed_online_orders.count()
#     online_revenue = confirmed_online_orders.aggregate(
#         total=Coalesce(Sum('final_amount'), 0)
#     )['total']

#     total_orders = pos_total + online_total

#     # ✅ Low Stock
#     low_stock_queryset = Item.objects.filter(item_quantity__lt=10).order_by('item_quantity')
#     low_stock_paginator = Paginator(low_stock_queryset, 5)
#     low_stock_page_number = request.GET.get('low_stock_page')
#     low_stock_items = low_stock_paginator.get_page(low_stock_page_number)
#     low_stock_count = low_stock_queryset.count()

#     # ✅ Expiring Items
#     today = datetime.date.today()
#     expiring_queryset = Item.objects.filter(exp_date__lte=today + datetime.timedelta(days=90)).order_by('exp_date')
#     expiring_paginator = Paginator(expiring_queryset, 5)
#     expiring_page_number = request.GET.get('expiring_page')
#     expiring_items = expiring_paginator.get_page(expiring_page_number)
#     expiring_count = expiring_queryset.count()

#     for order in online_orders_list:
#         if not order.name:
#             order.name = order.user.username

#     dashboard_stats = [
#         {
#             'label': 'Total Orders',
#             'icon': '💊',
#             'bg': 'bg-blue-100',
#             'text': 'text-blue-600',
#             'value': total_orders
#         },
#         {
#             'label': 'POS Orders',
#             'icon': '🏷️',
#             'bg': 'bg-green-100',
#             'text': 'text-green-600',
#             'value': pos_total
#         },
#         {
#             'label': 'Online Orders',
#             'icon': '🌐',
#             'bg': 'bg-purple-100',
#             'text': 'text-purple-600',
#             'value': online_total
#         },
#         {
#             'label': 'POS Revenue',
#             'icon': '💰',
#             'bg': 'bg-green-100',
#             'text': 'text-green-600',
#             'value': f"{pos_revenue} Ks"
#         },
#         {
#             'label': 'Online Revenue',
#             'icon': '💳',
#             'bg': 'bg-yellow-100',
#             'text': 'text-yellow-600',
#             'value': f"{online_revenue} Ks"
#         },
#         {
#             'label': 'Low Stock Items',
#             'icon': '⚠️',
#             'bg': 'bg-red-100',
#             'text': 'text-red-600',
#             'value': low_stock_count
#         },
#     ]

#     context = {
#         'dashboard_stats': dashboard_stats,
#         'low_stock_items': low_stock_items,
#         'expiring_items': expiring_items,
#         'online_orders_list': online_orders_list,
#         'expiring_count': expiring_count,
#     }

#     return render(request, 'pharmacist/dashboard.html', context)


@login_required
def pharmacist_dashboard_view(request):
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden("Unauthorized")

    # ✅ Keep existing GET params for pagination links
    qs = request.GET.copy()
    if 'page' in qs:
        qs.pop('page')
    if 'low_stock_page' in qs:
        qs.pop('low_stock_page')
    if 'expiring_page' in qs:
        qs.pop('expiring_page')
    qs = qs.urlencode()

    # ✅ POS Orders
    pos_orders = Cart.objects.filter(payment_method__in=['cash', 'mobile', 'print'])
    pos_total = pos_orders.count()
    pos_revenue = pos_orders.aggregate(total=Coalesce(Sum('total_amount'), 0))['total']

    # ✅ Online Orders
    online_orders_queryset = (
        Sale.objects
        .exclude(user__userprofile__role='pharmacist')
        .select_related('user')
        .order_by('-created_date')
    )

    paginator = Paginator(online_orders_queryset, 5)
    page_number = request.GET.get('page')
    online_orders_list = paginator.get_page(page_number)

    # ✅ Only confirmed orders counted for totals
    confirmed_online_orders = online_orders_queryset.filter(status='confirmed')
    online_total = confirmed_online_orders.count()
    online_revenue = confirmed_online_orders.aggregate(
        total=Coalesce(Sum('final_amount'), 0)
    )['total']

    total_orders = pos_total + online_total

    # ✅ Low Stock
    low_stock_queryset = Item.objects.filter(item_quantity__lt=10).order_by('item_quantity')
    low_stock_paginator = Paginator(low_stock_queryset, 5)
    low_stock_page_number = request.GET.get('low_stock_page')
    low_stock_items = low_stock_paginator.get_page(low_stock_page_number)
    low_stock_count = low_stock_queryset.count()

    # ✅ Expiring Items
    today = datetime.date.today()
    expiring_queryset = Item.objects.filter(exp_date__lte=today + datetime.timedelta(days=90)).order_by('exp_date')
    expiring_paginator = Paginator(expiring_queryset, 5)
    expiring_page_number = request.GET.get('expiring_page')
    expiring_items = expiring_paginator.get_page(expiring_page_number)
    expiring_count = expiring_queryset.count()

    for order in online_orders_list:
        if not order.name:
            order.name = order.user.username

    dashboard_stats = [
        {
            'label': 'Total Orders',
            'icon': '💊',
            'bg': 'bg-blue-100',
            'text': 'text-blue-600',
            'value': total_orders
        },
        {
            'label': 'POS Orders',
            'icon': '🏷️',
            'bg': 'bg-green-100',
            'text': 'text-green-600',
            'value': pos_total
        },
        {
            'label': 'Online Orders',
            'icon': '🌐',
            'bg': 'bg-purple-100',
            'text': 'text-purple-600',
            'value': online_total
        },
        {
            'label': 'POS Revenue',
            'icon': '💰',
            'bg': 'bg-green-100',
            'text': 'text-green-600',
            'value': f"{pos_revenue} Ks"
        },
        {
            'label': 'Online Revenue',
            'icon': '💳',
            'bg': 'bg-yellow-100',
            'text': 'text-yellow-600',
            'value': f"{online_revenue} Ks"
        },
        {
            'label': 'Low Stock Items',
            'icon': '⚠️',
            'bg': 'bg-red-100',
            'text': 'text-red-600',
            'value': low_stock_count
        },
    ]

    context = {
        'dashboard_stats': dashboard_stats,
        'low_stock_items': low_stock_items,
        'expiring_items': expiring_items,
        'online_orders_list': online_orders_list,
        'expiring_count': expiring_count,
        'qs': qs,  # ✅ Added for pagination links
    }

    return render(request, 'pharmacist/dashboard.html', context)


@login_required
def get_order_details(request, order_id):
    try:
        order = Sale.objects.get(id=order_id)
        items = SaleItem.objects.filter(sale=order)
        data = {
            "customer": order.name or order.user.username,
            "invoice": order.invoice_no,
            "total_amount": order.final_amount,
            "items": [
                {
                    "item_name": i.item.item_name,
                    "qty": i.quantity,
                    "price": i.price,
                    "subtotal": i.price * i.quantity
                } for i in items
            ]
        }
        return JsonResponse(data)
    except Sale.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)
    
from django.db import transaction



# views.py
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
def confirm_order_view(request, sale_id):
    # Pharmacist only
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden()

    # Pending orders only
    sale = get_object_or_404(Sale, id=sale_id, status='pending')

    # Pull items + promo relation to avoid n+1
    sale_items = (
        SaleItem.objects
        .select_related('item', 'promotion')
        .filter(sale=sale)
    )

    try:
        with transaction.atomic():
            # FIFO consume per SaleItem
            for si in sale_items:
                use_promo = bool(getattr(si, "is_promotion", False) and si.promotion_id)
                consume_fifo(
                    item=si.item,
                    qty=si.quantity,
                    sale_item=si,
                    use_promo=use_promo,
                    promotion=si.promotion if use_promo else None,
                    note_prefix=f"Invoice {sale.invoice_no}: "
                )

            # Mark order confirmed only after all stock ops succeed
            sale.status = 'confirmed'
            sale.save(update_fields=['status'])

            # Notify customer once
            Notification.objects.create(
                recipient=sale.user,
                message=f"Your order {sale.invoice_no} has been confirmed by the pharmacist."
            )

        messages.success(request, "Order confirmed and stock deducted (batch FIFO).")

    except Exception as e:
        messages.error(request, f"Stock error: {e}")
        return redirect('pharmacist_dashboard')

    return redirect('pharmacist_dashboard')

@login_required
def cancel_order_view(request, order_id):
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden()

    try:
        order = Sale.objects.get(id=order_id)

        # Only allow pending
        if order.status != 'pending':
            messages.warning(request, "Order already processed.")
            return redirect('pharmacist_dashboard')

        order.status = 'cancelled'
        order.save()

        Notification.objects.create(
            recipient=order.user,
            message=f"Your order {order.invoice_no} has been cancelled by the pharmacist."
        )

        messages.warning(request, "Order cancelled.")
    except Sale.DoesNotExist:
        messages.error(request, "Order not found.")

    return redirect('pharmacist_dashboard')




@login_required
def customer_dashboard_view(request):
    user = request.user
    
    filter_type = request.GET.get('notifications', 'unread')  # ✅ Step 1: Get the filter type
    items = Item.objects.all().order_by('-id')[:4]
    cart = Cart.objects.filter(user=user).last()
    cart_products = CartProduct.objects.filter(cart=cart) if cart else []

    total_orders = Sale.objects.filter(user=user, status='confirmed').count()
    total_items = SaleItem.objects.filter(sale__user=user, sale__status= 'confirmed').aggregate(total=Coalesce(Sum('quantity'), 0))['total']
    total_spent = Sale.objects.filter(user=user, status='confirmed').aggregate(spent=Coalesce(Sum('final_amount'), 0))['spent']
    categories = Category.objects.all()

    # ✅ Step 2: Filter notifications based on tab
    if filter_type == 'all':
        notifications = Notification.objects.filter(recipient=user).order_by('-created_at')
    else:  # default to unread
        notifications = Notification.objects.filter(recipient=user, is_read=False).order_by('-created_at')

    dashboard_stats = [
        {
            'label': 'Total Orders',
            'icon': 'fa-box',
            'bg_class': 'from-blue-500 to-blue-600',
            'value': total_orders
        },
        {
            'label': 'Items Purchased',
            'icon': 'fa-shopping-basket',
            'bg_class': 'from-green-500 to-green-600',
            'value': total_items
        },
        {
            'label': 'Total Spent',
            'icon': 'fa-dollar-sign',
            'bg_class': 'from-yellow-400 to-yellow-500',
            'value': f"{total_spent} Ks"
        },
    ]

    context = {
        'dashboard_stats': dashboard_stats,
        'items': items,
        'cart': cart,
        'cart_products': cart_products,
        'notifications': notifications,
        'categories':categories,
        'filter_type': filter_type,
        
        # any other context data needed
    }
    return render(request, 'customer/dashboard.html', context)


@login_required
def mark_notification_read(request, noti_id):
    notification = get_object_or_404(Notification, id=noti_id, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    return redirect('customer_dashboard')
@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('customer_dashboard')



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Sum, Count, F, FloatField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
import json

from .models import Cart, CartProduct, Sale, SaleItem, Item

# @login_required
# def report_view(request):
#     if request.user.userprofile.role != 'pharmacist':
#         return HttpResponseForbidden("Pharmacists only.")

#     filter_type = request.GET.get('filter', 'yearly')
#     today = now().date()

#     # ✅ Confirmed Online Orders Filter
#     confirmed_online_orders = Sale.objects.exclude(user__userprofile__role='pharmacist')\
#                                           .filter(status='confirmed')

#     if filter_type == 'daily':
#         confirmed_online_orders = confirmed_online_orders.filter(created_date__date=today)
#     elif filter_type == 'weekly':
#         start_week = today - timedelta(days=today.weekday())
#         end_week = start_week + timedelta(days=6)
#         confirmed_online_orders = confirmed_online_orders.filter(created_date__date__range=(start_week, end_week))
#     elif filter_type == 'monthly':
#         confirmed_online_orders = confirmed_online_orders.filter(created_date__month=today.month, created_date__year=today.year)
#     elif filter_type == 'yearly':
#         confirmed_online_orders = confirmed_online_orders.filter(created_date__year=today.year)

#     confirmed_online_orders = confirmed_online_orders.order_by('-created_date')

#     # ✅ POS Orders
#     pos_orders = Cart.objects.filter(payment_method__in=['cash', 'mobile', 'print']).order_by('-created_date')
#     pos_transactions = pos_orders.count()
#     pos_revenue = pos_orders.aggregate(total=Coalesce(Sum('total_amount'), 0))['total']

#     for order in pos_orders:
#         if not order.customer_name:
#             order.customer_name = "Customer"

#     # ✅ Pagination
#     pos_page_number = request.GET.get('pos_page')
#     pos_paginator = Paginator(pos_orders, 10)
#     pos_orders_page = pos_paginator.get_page(pos_page_number)

#     online_page_number = request.GET.get('online_page')
#     online_paginator = Paginator(confirmed_online_orders, 10)
#     online_orders_page = online_paginator.get_page(online_page_number)

#     # ✅ Top Selling POS Products
#     top_pos_products = (
#         CartProduct.objects
#         .values('item_id', 'item__item_name', category_name=F('item__category__name'))
#         .annotate(total_qty=Sum('qty'), total_revenue=Sum('price'))
#         .order_by('-total_qty')[:5]
#     )

#     # ✅ Top Selling Online Products (confirmed only)
#     top_online_products = (
#         SaleItem.objects
#         .filter(sale__status='confirmed')
#         .values('item_id', 'item__item_name', category_name=F('item__category__name'))
#         .annotate(total_qty=Sum('quantity'), total_revenue=Sum('price'))
#         .order_by('-total_qty')[:5]
#     )

#     # ✅ Chart Data
#     pos_chart_labels = json.dumps([p['item__item_name'] for p in top_pos_products])
#     pos_chart_data = json.dumps([p['total_qty'] for p in top_pos_products])
#     online_chart_labels = json.dumps([p['item__item_name'] for p in top_online_products])
#     online_chart_data = json.dumps([p['total_qty'] for p in top_online_products])

#     # ✅ Item Sold
#     pos_items_sold = CartProduct.objects.aggregate(total_qty=Coalesce(Sum('qty'), 0))['total_qty']
#     online_items_sold = SaleItem.objects.filter(sale__status='confirmed')\
#                                         .aggregate(total=Coalesce(Sum('quantity'), 0))['total']
#     items_sold = pos_items_sold + online_items_sold

#     # ✅ Avg. Margin (POS only)
#     cart_products = CartProduct.objects.annotate(
#         margin=ExpressionWrapper(
#             (F('price') - F('item__purcharse_price')) / F('item__purcharse_price') * 100.0,
#             output_field=FloatField()
#         )
#     )
#     margin_data = cart_products.aggregate(
#         total_margin=Coalesce(Sum('margin'), 0.0),
#         count=Coalesce(Count('id'), 1)
#     )
#     avg_margin = round(margin_data['total_margin'] / margin_data['count'], 2)

#     # ✅ Revenue and Transactions
#     online_transactions = confirmed_online_orders.count()
#     online_revenue = confirmed_online_orders.aggregate(total=Coalesce(Sum('final_amount'), 0))['total']
#     total_transactions = pos_transactions + online_transactions
#     total_revenue = pos_revenue + online_revenue

#     # ✅ Summary Cards
#     summary_list = [
#         {
#             'label': 'POS Transactions',
#             'icon': 'fa-receipt',
#             'bg': 'bg-blue-100',
#             'text': 'text-blue-600',
#             'value': pos_transactions,
#         },
#         {
#             'label': 'Online Transactions',
#             'icon': 'fa-receipt',
#             'bg': 'bg-blue-100',
#             'text': 'text-blue-600',
#             'value': online_transactions,
#         },
#         {
#             'label': 'POS Revenue',
#             'icon': 'fa-dollar-sign',
#             'bg': 'bg-green-100',
#             'text': 'text-green-600',
#             'value': pos_revenue,
#             'unit': 'Ks',
#         },
#         {
#             'label': 'Online Revenue',
#             'icon': 'fa-dollar-sign',
#             'bg': 'bg-green-100',
#             'text': 'text-green-600',
#             'value': online_revenue,
#             'unit': 'Ks',
#         },
#         {
#             'label': 'Items Sold',
#             'icon': 'fa-shopping-basket',
#             'bg': 'bg-purple-100',
#             'text': 'text-purple-600',
#             'value': items_sold,
#         },
#         {
#             'label': 'Avg. Margin',
#             'icon': 'fa-percentage',
#             'bg': 'bg-yellow-100',
#             'text': 'text-yellow-600',
#             'value': avg_margin,
#             'unit': '%',
#         },
#     ]

#     return render(request, 'report.html', {
#         'filter_type': filter_type,
#         'summary_list': summary_list,
#         'top_pos_products': top_pos_products,
#         'top_online_products': top_online_products,
#         'pos_chart_labels': pos_chart_labels,
#         'pos_chart_data': pos_chart_data,
#         'online_chart_labels': online_chart_labels,
#         'online_chart_data': online_chart_data,
#         'pos_orders_list': pos_orders,
#         'pos_transactions': pos_transactions,
#         'pos_revenue': pos_revenue,
#         'pos_orders_page': pos_orders_page,
#         'online_orders_list': confirmed_online_orders,
#         'online_transactions': online_transactions,
#         'online_revenue': online_revenue,
#         'online_orders_page': online_orders_page,
#         'total_transactions': total_transactions,
#         'total_revenue': total_revenue,
#         'items_sold': items_sold,
#         'avg_margin': avg_margin,
#     })





from django.db.models import Sum, Count, F, Value, FloatField, ExpressionWrapper, Case, When
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from datetime import timedelta
import json

@login_required
def report_view(request):
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden("Pharmacists only.")

    filter_type = request.GET.get('filter', 'yearly')
    now = timezone.now()

    # --- Python-side date range filtering ---
    if filter_type == "daily":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif filter_type == "weekly":
        start_date = now - timedelta(days=now.weekday())
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
    elif filter_type == "monthly":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif filter_type == "yearly":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    else:
        start_date = None
        end_date = None

    # --- POS Orders ---
    pos_orders = Cart.objects.filter(payment_method__in=['cash', 'mobile', 'print'])
    if start_date and end_date:
        pos_orders = pos_orders.filter(created_date__range=(start_date, end_date))
    pos_orders = pos_orders.order_by('-created_date')

    pos_transactions = pos_orders.count()
    pos_revenue = pos_orders.aggregate(total=Coalesce(Sum('total_amount'), 0))['total']

    for order in pos_orders:
        if not order.customer_name:
            order.customer_name = "Customer"

    # --- Online Orders (Confirmed only) ---
    confirmed_online_orders = Sale.objects.exclude(
        user__userprofile__role='pharmacist'
    ).filter(status='confirmed')
    if start_date and end_date:
        confirmed_online_orders = confirmed_online_orders.filter(created_date__range=(start_date, end_date))
    confirmed_online_orders = confirmed_online_orders.order_by('-created_date')

    online_transactions = confirmed_online_orders.count()
    online_revenue = confirmed_online_orders.aggregate(total=Coalesce(Sum('final_amount'), 0))['total']

    # --- Pagination ---
    pos_orders_page = Paginator(pos_orders, 10).get_page(request.GET.get('pos_page'))
    online_orders_page = Paginator(confirmed_online_orders, 10).get_page(request.GET.get('online_page'))

    # --- Top Selling Products ---
    top_pos_products = CartProduct.objects.filter(cart__in=pos_orders)\
        .values('item_id', 'item__item_name', category_name=F('item__category__name'))\
        .annotate(total_qty=Sum('qty'), total_revenue=Sum('price'))\
        .order_by('-total_qty')[:5]

    top_online_products = SaleItem.objects.filter(sale__in=confirmed_online_orders)\
        .values('item_id', 'item__item_name', category_name=F('item__category__name'))\
        .annotate(total_qty=Sum('quantity'), total_revenue=Sum('price'))\
        .order_by('-total_qty')[:5]

    # --- Chart Data ---
    pos_chart_labels = json.dumps([p['item__item_name'] for p in top_pos_products])
    pos_chart_data = json.dumps([p['total_qty'] for p in top_pos_products])
    online_chart_labels = json.dumps([p['item__item_name'] for p in top_online_products])
    online_chart_data = json.dumps([p['total_qty'] for p in top_online_products])

    # --- Items Sold ---
    pos_items_sold = CartProduct.objects.filter(cart__in=pos_orders)\
        .aggregate(total_qty=Coalesce(Sum('qty'), 0))['total_qty']
    online_items_sold = SaleItem.objects.filter(sale__in=confirmed_online_orders)\
        .aggregate(total=Coalesce(Sum('quantity'), 0))['total']
    items_sold = pos_items_sold + online_items_sold

    # --- Avg. Margin ---
    pos_margins = CartProduct.objects.filter(cart__in=pos_orders).annotate(
        margin=Case(
            When(item__purcharse_price=0, then=Value(0.0)),
            default=(F('price') - F('item__purcharse_price')) / F('item__purcharse_price') * 100.0,
            output_field=FloatField()
        )
    )
    online_margins = SaleItem.objects.filter(sale__in=confirmed_online_orders).annotate(
        margin=Case(
            When(item__purcharse_price=0, then=Value(0.0)),
            default=(F('price') - F('item__purcharse_price')) / F('item__purcharse_price') * 100.0,
            output_field=FloatField()
        )
    )
    total_margin_sum = pos_margins.aggregate(sum=Coalesce(Sum('margin'), 0.0))['sum'] + \
                       online_margins.aggregate(sum=Coalesce(Sum('margin'), 0.0))['sum']
    total_margin_count = pos_margins.aggregate(count=Coalesce(Count('id'), 0))['count'] + \
                         online_margins.aggregate(count=Coalesce(Count('id'), 0))['count']
    avg_margin = round(total_margin_sum / total_margin_count, 2) if total_margin_count > 0 else 0.0

    # --- Summary Cards ---
    summary_list = [
        {'label': 'POS Transactions', 'icon': 'fa-receipt', 'bg': 'bg-blue-100', 'text': 'text-blue-600', 'value': pos_transactions},
        {'label': 'Online Transactions', 'icon': 'fa-receipt', 'bg': 'bg-blue-100', 'text': 'text-blue-600', 'value': online_transactions},
        {'label': 'POS Revenue', 'icon': 'fa-dollar-sign', 'bg': 'bg-green-100', 'text': 'text-green-600', 'value': pos_revenue, 'unit': 'Ks'},
        {'label': 'Online Revenue', 'icon': 'fa-dollar-sign', 'bg': 'bg-green-100', 'text': 'text-green-600', 'value': online_revenue, 'unit': 'Ks'},
        {'label': 'Items Sold', 'icon': 'fa-shopping-basket', 'bg': 'bg-purple-100', 'text': 'text-purple-600', 'value': items_sold},
        {'label': 'Avg. Margin', 'icon': 'fa-percentage', 'bg': 'bg-yellow-100', 'text': 'text-yellow-600', 'value': avg_margin, 'unit': '%'},
    ]

    return render(request, 'report.html', {
        'filter_type': filter_type,  # HTML filter comparison fix
        'summary_list': summary_list,
        'top_pos_products': top_pos_products,
        'top_online_products': top_online_products,
        'pos_chart_labels': pos_chart_labels,
        'pos_chart_data': pos_chart_data,
        'online_chart_labels': online_chart_labels,
        'online_chart_data': online_chart_data,
        'pos_orders_list': pos_orders_page,
        'online_orders_list': online_orders_page,
        'total_transactions': pos_transactions + online_transactions,
        'total_revenue': pos_revenue + online_revenue,
        'items_sold': items_sold,
        'avg_margin': avg_margin,
        'pos_transactions': pos_transactions,
        'pos_revenue': pos_revenue,
        'online_transactions': online_transactions,
        'online_revenue': online_revenue,
    })


@csrf_exempt
def edit_item_view(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == "POST":
        item.item_name = request.POST.get('item_name')
        item.strength = request.POST.get('strength')
        item.item_quantity = request.POST.get('item_quantity')
        item.item_price = request.POST.get('item_price')
        item.is_limited = request.POST.get('is_limited') == 'true'
        item.save()
        return redirect('medicine_diseaseview')
    


def delete_item(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(Item, id=item_id)
        item.delete()
        messages.success(request, f"{item.item_name} deleted successfully.")
    return redirect('medicine_diseaseview')  # your template name


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
import datetime

# models imported already in your file:
# from .models import Item, Category, Cart, CartProduct, StockHistory, Supplier, etc.

# @login_required
# def inventory_view(request):
#     # Role check
#     if request.user.userprofile.role != 'pharmacist':
#         messages.error(request, "You do not have permission to access this page.")
#         return redirect('login')

#     # Query items & compute days_left
#     items_queryset = Item.objects.all().order_by('-id')
#     for item in items_queryset:
#         if item.exp_date:
#             item.days_left = (item.exp_date - datetime.date.today()).days
#         else:
#             item.days_left = None

#     # Categories queryset
#     categories_queryset = Category.objects.all().order_by('name')

#     # ---------------------- Pagination for Items ----------------------
#     items_paginator = Paginator(items_queryset, 10)  # 10 items per page
#     items_page_number = request.GET.get('items_page')
#     items = items_paginator.get_page(items_page_number)

#     # ---------------------- Pagination for Categories ----------------------
#     categories_paginator = Paginator(categories_queryset, 5)  # 5 categories per page
#     categories_page_number = request.GET.get('categories_page')
#     categories = categories_paginator.get_page(categories_page_number)

#     # ---------------------- CATEGORY CREATE ----------------------
#     if request.method == 'POST':
#         # Create new category
#         if 'save_category' in request.POST and request.POST.get('save_category'):
#             name = request.POST.get('category_name', '').strip()
#             description = request.POST.get('category_description', '').strip()
#             if name:
#                 Category.objects.create(name=name, description=description)
#                 messages.success(request, "Category added successfully.")
#             else:
#                 messages.error(request, "Category name is required.")
#             return redirect('inventory_view')

#         # Update existing category
#         if 'update_category' in request.POST and request.POST.get('update_category'):
#             category_id = request.POST.get('category_id')
#             name = request.POST.get('category_name', '').strip()
#             description = request.POST.get('category_description', '').strip()
#             if not category_id:
#                 messages.error(request, "Invalid category.")
#                 return redirect('inventory_view')
#             category = get_object_or_404(Category, id=category_id)
#             if name:
#                 category.name = name
#                 category.description = description
#                 category.save()
#                 messages.success(request, "Category updated successfully.")
#             else:
#                 messages.error(request, "Category name is required.")
#             return redirect('inventory_view')

#         # Delete category (safe: prevent delete if items exist)
#         if 'delete_category' in request.POST and request.POST.get('delete_category'):
#             category_id = request.POST.get('delete_category')
#             category = get_object_or_404(Category, id=category_id)
#             # Prevent deleting category that still has items
#             if Item.objects.filter(category=category).exists():
#                 messages.error(request, "Cannot delete category with items. Reassign or delete items first.")
#             else:
#                 category.delete()
#                 messages.success(request, "Category deleted successfully.")
#             return redirect('inventory_view')

#         # ---------------------- ITEM CREATE OR EDIT ----------------------
#         if 'save_item' in request.POST:
#             item_id = request.POST.get('item_id')
#             is_edit = bool(item_id)

#             try:
#                 category = Category.objects.get(id=request.POST.get('category'))
#             except Category.DoesNotExist:
#                 messages.error(request, "Invalid category.")
#                 return redirect('inventory_view')

#             # Prepare cleaned data
#             data = {
#                 'category': category,
#                 'item_name': request.POST.get('item_name'),
#                 'item_quantity': request.POST.get('item_quantity') or 0,
#                 'item_price': request.POST.get('item_price') or 0,
#                 'purcharse_price': request.POST.get('purcharse_price') or 0,
#                 'item_description': request.POST.get('item_description') or '',
#                 'exp_date': parse_date(request.POST.get('exp_date')) if request.POST.get('exp_date') else None,
#                 'brand_name': request.POST.get('brand_name') or '',
#                 'batch_number': request.POST.get('batch_number') or '',
#                 'stock_minimum': request.POST.get('stock_minimum') or 10,
#                 'is_limited': 'is_limited' in request.POST,
#                 'max_quantity': request.POST.get('max_quantity') or 5,
#             }

#             # Get image from FILES
#             item_photo = request.FILES.get('item_photo')
#             if item_photo:
#                 data['item_photo'] = item_photo

#             if is_edit:
#                 item = get_object_or_404(Item, id=item_id)
#                 for field, value in data.items():
#                     setattr(item, field, value)
#                 item.save()
#                 messages.success(request, "Item updated successfully.")
#             else:
#                 if not item_photo:
#                     messages.error(request, "Medication image is required.")
#                     return redirect('inventory_view')
#                 Item.objects.create(**data)
#                 messages.success(request, "Item created successfully.")
#             return redirect('inventory_view')

#         # ---------------------- ITEM DELETE ----------------------
#         if 'delete_item' in request.POST:
#             item_id = request.POST.get('delete_item')
#             item = get_object_or_404(Item, id=item_id)
#             item.delete()
#             messages.success(request, "Item deleted successfully.")
#             return redirect('inventory_view')

#     # ---------------------- Pagination & other lists (GET render) ----------------------
#     # Low stock
#     low_stock_queryset = Item.objects.filter(item_quantity__lt=10).order_by('item_quantity')
#     low_stock_paginator = Paginator(low_stock_queryset, 5)
#     low_stock_page_number = request.GET.get('low_stock_page')
#     low_stock_items = low_stock_paginator.get_page(low_stock_page_number)
#     low_stock_count = low_stock_queryset.count()

#     # Expiring
#     today = datetime.date.today()
#     expiring_queryset = Item.objects.filter(exp_date__lte=today + datetime.timedelta(days=90)).order_by('exp_date')
#     expiring_paginator = Paginator(expiring_queryset, 5)
#     expiring_page_number = request.GET.get('expiring_page')
#     expiring_items = expiring_paginator.get_page(expiring_page_number)
#     expiring_count = expiring_queryset.count()

#     return render(request, 'inventory.html', {
#         'items': items,
#         'categories': categories,
#         'low_stock_items': low_stock_items,
#         'low_stock_count': low_stock_count,
#         'low_stock_page_number': low_stock_page_number,
#         'expiring_items': expiring_items,
#         'expiring_count': expiring_count,
#     })



from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date
from django.utils import timezone
import datetime

# models import
# from .models import Item, Category

@login_required
def inventory_view(request):
    # Role check
    if request.user.userprofile.role != 'pharmacist':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('login')

    # ---------- Filters from GET ----------
    filter_type = request.GET.get('filter')           # None | 'low' | 'expiring'
    expiring_days = request.GET.get('days') or 90     # expiring window days
    try:
        expiring_days = int(expiring_days)
        if expiring_days <= 0:
            expiring_days = 90
    except ValueError:
        expiring_days = 90

    focus_id = request.GET.get('focus_id')            # item id to focus & jump
    items_page_number = request.GET.get('items_page') # main items page
    categories_page_number = request.GET.get('categories_page')

    # ---------- Base Querysets ----------
    # Items (DESC by id)
    items_queryset = Item.objects.all().order_by('-id')
    # Apply filter if provided
    if filter_type == 'low':
        # same condition with dashboard/widgets
        items_queryset = items_queryset.filter(item_quantity__lt=10)
    elif filter_type == 'expiring':
        today = datetime.date.today()
        items_queryset = items_queryset.filter(exp_date__lte=today + datetime.timedelta(days=expiring_days))

    # Add days_left attribute for display (optional)
    for it in items_queryset:
        it.days_left = (it.exp_date - datetime.date.today()).days if it.exp_date else None

    # Categories queryset (alphabetical)
    categories_queryset = Category.objects.all().order_by('name')

    # ---------- Pagination: Items ----------
    per_page = 10
    items_paginator = Paginator(items_queryset, per_page)

    # If focus_id is provided and the item exists inside CURRENT filtered queryset,
    # jump to the page that contains it (remember: ordering is '-id')
    if focus_id:
        try:
            f_id = int(focus_id)
            if items_queryset.filter(id=f_id).exists():
                # Count how many rows (in current filtered queryset) have id > focus_id (because '-id' order)
                before_count = items_queryset.filter(id__gt=f_id).count()
                items_page_number = (before_count // per_page) + 1
        except (ValueError, TypeError):
            pass

    items = items_paginator.get_page(items_page_number)

    # ---------- Pagination: Categories ----------
    categories_paginator = Paginator(categories_queryset, 5)
    categories = categories_paginator.get_page(categories_page_number)

    # ---------- POST: CATEGORY CRUD ----------
    if request.method == 'POST':
        # Create new category
        if 'save_category' in request.POST and request.POST.get('save_category'):
            name = request.POST.get('category_name', '').strip()
            description = request.POST.get('category_description', '').strip()
            if name:
                Category.objects.create(name=name, description=description)
                messages.success(request, "Category added successfully.")
            else:
                messages.error(request, "Category name is required.")
            return redirect('inventory_view')

        # Update existing category
        if 'update_category' in request.POST and request.POST.get('update_category'):
            category_id = request.POST.get('category_id')
            name = request.POST.get('category_name', '').strip()
            description = request.POST.get('category_description', '').strip()


            if not category_id:
                messages.error(request, "Invalid category.")
                return redirect('inventory_view')
            category = get_object_or_404(Category, id=category_id)
            if name:
                category.name = name
                category.description = description
                category.save()
                messages.success(request, "Category updated successfully.")
            else:
                messages.error(request, "Category name is required.")
            return redirect('inventory_view')

        # Delete category (safe: prevent delete if items exist)
        if 'delete_category' in request.POST and request.POST.get('delete_category'):
            category_id = request.POST.get('delete_category')
            category = get_object_or_404(Category, id=category_id)
            if Item.objects.filter(category=category).exists():
                messages.error(request, "Cannot delete category with items. Reassign or delete items first.")
            else:
                category.delete()
                messages.success(request, "Category deleted successfully.")
            return redirect('inventory_view')

        # ---------- ITEM CREATE OR EDIT ----------
        if 'save_item' in request.POST:
            item_id = request.POST.get('item_id')
            is_edit = bool(item_id)

            try:
                category = Category.objects.get(id=request.POST.get('category'))
            except Category.DoesNotExist:
                messages.error(request, "Invalid category.")
                return redirect('inventory_view')

            data = {
                'category': category,
                'item_name': request.POST.get('item_name'),
                'item_quantity': request.POST.get('item_quantity') or 0,
                'item_price': request.POST.get('item_price') or 0,
                'purcharse_price': request.POST.get('purcharse_price') or 0,
                'item_description': request.POST.get('item_description') or '',
                'exp_date': parse_date(request.POST.get('exp_date')) if request.POST.get('exp_date') else None,
                'brand_name': request.POST.get('brand_name') or '',
                'batch_number': request.POST.get('batch_number') or '',
                'stock_minimum': request.POST.get('stock_minimum') or 10,
                'is_limited': 'is_limited' in request.POST,
                'max_quantity': request.POST.get('max_quantity') or 5,
            }

            # file
            item_photo = request.FILES.get('item_photo')
            if item_photo:
                data['item_photo'] = item_photo

            if is_edit:
                item = get_object_or_404(Item, id=item_id)
                for field, value in data.items():
                    setattr(item, field, value)
                item.save()
                messages.success(request, "Item updated successfully.")
            else:
                if not item_photo:
                    messages.error(request, "Medication image is required.")
                    return redirect('inventory_view')
                Item.objects.create(**data)
                messages.success(request, "Item created successfully.")
            return redirect('inventory_view')

        # ---------- ITEM DELETE ----------
        if 'delete_item' in request.POST:
            item_id = request.POST.get('delete_item')
            item = get_object_or_404(Item, id=item_id)
            item.delete()
            messages.success(request, "Item deleted successfully.")
            return redirect('inventory_view')

    # ---------- (Side widgets) Low stock & Expiring lists ----------
    low_stock_queryset = Item.objects.filter(item_quantity__lt=10).order_by('item_quantity')
    low_stock_paginator = Paginator(low_stock_queryset, 5)
    low_stock_page_number = request.GET.get('low_stock_page')
    low_stock_items = low_stock_paginator.get_page(low_stock_page_number)
    low_stock_count = low_stock_queryset.count()


    today = datetime.date.today()
    expiring_queryset = Item.objects.filter(exp_date__lte=today + datetime.timedelta(days=90)).order_by('exp_date')
    expiring_paginator = Paginator(expiring_queryset, 5)
    expiring_page_number = request.GET.get('expiring_page')
    expiring_items = expiring_paginator.get_page(expiring_page_number)
    expiring_count = expiring_queryset.count()

    # ---------- Keep querystring for pagination links ----------
    qd = request.GET.copy()
    for key in ['items_page', 'categories_page', 'low_stock_page', 'expiring_page']:
        if key in qd:
            del qd[key]
    qs = qd.urlencode()  # e.g. "filter=low&focus_id=123"

    return render(request, 'inventory.html', {
        'items': items,
        'categories': categories,
        'low_stock_items': low_stock_items,
        'low_stock_count': low_stock_count,
        'expiring_items': expiring_items,
        'expiring_count': expiring_count,
        'filter_type': filter_type,
        'expiring_days': expiring_days,
        'qs': qs,  # use this to append to pagination links
    })




@login_required
def send_to_promotion(request):
    if request.method != "POST":
        return redirect("inventory_view")

    item_id = request.POST.get("item_id")
    qty = int(request.POST.get("quantity") or 0)
    discount = int(request.POST.get("discount") or 0)

    item = get_object_or_404(Item, id=item_id)

    # quick guard using legacy field
    if qty <= 0:
        messages.error(request, "Quantity must be greater than 0.")
        return redirect("inventory_view")
    if qty > item.item_quantity:
        messages.error(request, "Quantity cannot be greater than current stock.")
        return redirect("inventory_view")

    # 🚨 Extra Guard: Prevent expired item from going to promotion
    if item.exp_date and item.exp_date < timezone.now().date():
        messages.error(request, f"{item.item_name} သည် Expired ဖြစ်သဖြင့် promotion သို့ မပို့နိုင်ပါ။")
        return redirect("inventory_view")

    promo = PromotionItem.objects.create(
        item=item,
        quantity=qty,
        discount_percent=discount,
        expire_date=item.exp_date,
        status='active'
    )
    try:
        allocate_promotion_fifo(promo)  # reserve only; on_hand not deducted yet
    except Exception as e:
        promo.delete()
        messages.error(request, f"Allocation failed: {e}")
        return redirect("inventory_view")

    messages.success(request, f"{item.item_name} sent to promotion (reserved: {qty}).")
    return redirect("inventory_view")

@login_required
def cancel_promotion(request, promo_id):
    promo = get_object_or_404(PromotionItem, id=promo_id, status='active')

    with transaction.atomic():
        allocs = promo.allocations.select_for_update().select_related('batch')
        for a in allocs:
            b = a.batch
            # release reservation only
            b.reserved_promo = F('reserved_promo') - a.quantity
            b.save(update_fields=['reserved_promo'])
        promo.allocations.all().delete()
        promo.status = 'cancelled'
        promo.save(update_fields=['status'])

    messages.success(request, "Promotion cancelled and allocations released.")
    return redirect('promotion_area')  # change to your list view name



@login_required
def promotion_area(request):
    today = timezone.now().date()
    promotions = (
        PromotionItem.objects
        .select_related("item")
        .filter(status="active", quantity__gt=0)
        .filter(Q(expire_date__isnull=True) | Q(expire_date__gte=today))
    )
    return render(request, "promotion_area.html", {"promotions": promotions})

@login_required
def add_promo_to_cart(request, promo_id):
    promo = get_object_or_404(
        PromotionItem.objects.select_related("item"),
        id=promo_id, status="active"
    )

    try:
        qty = int(request.POST.get("qty", "1"))
    except ValueError:
        qty = 1
    if qty < 1:
        qty = 1
    if qty > promo.quantity:
        messages.error(request, f"Only {promo.quantity} left in promo stock.")
        return redirect("promotion_area")

    cart, _ = Cart.objects.get_or_create(user=request.user)
    unit_price = promo.discounted_price()

    cp = CartProduct.objects.create(
        cart=cart,
        item=promo.item,
        qty=qty,
        unit_price=unit_price,
        price=qty * unit_price
    )

    # save promo mapping in session
    promo_cart = request.session.get("promo_cart", {})
    promo_cart[str(cp.id)] = promo.id
    request.session["promo_cart"] = promo_cart
    request.session.modified = True

    cart.update_total_amount()
    messages.success(request, f"Added {qty} × {promo.item.item_name} (promo) to cart.")
    return redirect("promotion_area")


def _remove_cp_and_session(request, cp):
    cp_id_str = str(cp.id)
    cp.delete()
    promo_cart = request.session.get("promo_cart", {})
    if cp_id_str in promo_cart:
        promo_cart.pop(cp_id_str, None)
        request.session["promo_cart"] = promo_cart
        request.session.modified = True


def _get_promo_for_cp(request, cp):
    promo_cart = request.session.get("promo_cart", {})
    promo_id = promo_cart.get(str(cp.id))
    if not promo_id:
        return None
    try:
        return PromotionItem.objects.get(id=promo_id, status="active")
    except PromotionItem.DoesNotExist:
        promo_cart.pop(str(cp.id), None)
        request.session["promo_cart"] = promo_cart
        request.session.modified = True
        return None


# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from .models import (
    Item, StockBatch, PromotionItem, PromotionAllocation,
    StockHistory, Sale, SaleItem, SaleBatchConsumption
)

# ---------- FIFO: reserve for promotion (Admin sends to promotion) ----------
def allocate_promotion_fifo(promo: PromotionItem):
    if promo.status != 'active':
        raise ValueError("Promotion is not active")
    needed = int(promo.quantity or 0)
    if needed <= 0:
        raise ValueError("Promotion quantity must be > 0")

    with transaction.atomic():
        batches = (StockBatch.objects
                   .select_for_update()
                   .filter(item=promo.item)
                   .order_by('exp_date', 'id'))
        for b in batches:
            if needed <= 0:
                break
            take = min(needed, b.available)
            if take > 0:
                PromotionAllocation.objects.create(promotion=promo, batch=b, quantity=take)
                b.reserved_promo = F('reserved_promo') + take
                b.save(update_fields=['reserved_promo'])
                needed -= take
        if needed > 0:
            raise ValueError("Not enough available stock to allocate for this promotion")



def consume_fifo(item, qty, sale_item=None,
                 use_promo=False, promotion=None,
                 note_prefix=''):
    """
    FIFO stock consumption
    - item: Item object
    - qty: integer quantity to consume
    - sale_item: SaleItem (online) or None (POS)
    - use_promo: bool, True if promotion
    - promotion: PromotionItem object if use_promo=True
    - note_prefix: str, for StockHistory note
    """

    remaining = int(qty or 0)
    if remaining <= 0:
        return

    with transaction.atomic():
        if use_promo:
            # ✅ Promo: consume from reserved allocations first
            allocs = (
                PromotionAllocation.objects
                .select_for_update()
                .filter(promotion=promotion)
                .select_related('batch')
                .order_by('batch__exp_date', 'batch_id')
            )
            for a in allocs:
                if remaining <= 0:
                    break
                b = a.batch
                take = min(remaining, a.quantity, b.quantity_on_hand, b.reserved_promo)
                if take <= 0:
                    continue

                # reduce allocation
                new_qty = a.quantity - take
                if new_qty <= 0:
                    a.delete()
                else:
                    a.quantity = new_qty
                    a.save(update_fields=['quantity'])

                # reduce promo stock
                promotion.quantity = F('quantity') - take
                promotion.save(update_fields=['quantity'])

                # reduce batch
                b.quantity_on_hand = F('quantity_on_hand') - take
                b.reserved_promo = F('reserved_promo') - take
                b.save(update_fields=['quantity_on_hand', 'reserved_promo'])

                # log consumption
                if sale_item:
                    SaleBatchConsumption.objects.create(
                        sale_item=sale_item, batch=b, quantity=take
                    )
                StockHistory.objects.create(
                    item=item, action='out', quantity=take,
                    note=f"{note_prefix}Sale (promo) - batch {b.batch_number}"
                )
                remaining -= take

        else:
            # ✅ Normal: consume from available stock (oldest batch first)
            batches = (
                StockBatch.objects
                .select_for_update()
                .filter(item=item)
                .order_by('exp_date', 'id')
            )
            for b in batches:
                if remaining <= 0:
                    break
                take = min(remaining, b.available)
                if take <= 0:
                    continue

                b.quantity_on_hand = F('quantity_on_hand') - take
                b.save(update_fields=['quantity_on_hand'])

                if sale_item:
                    SaleBatchConsumption.objects.create(
                        sale_item=sale_item, batch=b, quantity=take
                    )
                StockHistory.objects.create(
                    item=item, action='out', quantity=take,
                    note=f"{note_prefix}Sale - batch {b.batch_number}"
                )
                remaining -= take

        if remaining > 0:
            raise ValueError("Insufficient stock to consume")

        # ✅ Update legacy fast field
        item.item_quantity = max(0, item.item_quantity - qty)
        item.save(update_fields=['item_quantity'])

# @login_required
# def order_view(request):
#     if request.user.userprofile.role != 'pharmacist':
#         messages.error(request, "You do not have permission to access this page.")
#         return redirect('pharmacist_dashboard')

#     category_id = request.GET.get('cid')
#     categories = Category.objects.all()
#     if category_id:
#         items = Item.objects.filter(category_id=category_id).order_by('-id') 
#     else:
#         items = Item.objects.all().order_by('-id') 
  
#     context = {
#         'categories': categories,
#         'items': items,
#     }
#     return render(request, 'POS.html', context)


# views.py (order_view ထဲ)
import json
from django.utils import timezone
from django.db.models import Q

def order_view(request):
    if request.user.userprofile.role != 'pharmacist':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('pharmacist_dashboard')

    category_id = request.GET.get('cid')
    search_query = request.GET.get('q', '')

    categories = Category.objects.all()
    items = Item.objects.all()
    if category_id:
        items = items.filter(category_id=category_id)
    if search_query:
        items = items.filter(item_name__icontains=search_query)
    items = items.order_by('-id')

    # ✅ Active promotions (earliest expiry per item)
    today = timezone.now().date()
    promos_qs = (PromotionItem.objects
                 .select_related('item')
                 .filter(status='active', quantity__gt=0)
                 .filter(Q(expire_date__isnull=True) | Q(expire_date__gte=today))
                 .filter(item__in=items)
                 .order_by('item_id', 'expire_date', 'id'))

    promos_map = {}
    for p in promos_qs:
        if p.item_id not in promos_map:  # take earliest-exp promotion per item
            promos_map[p.item_id] = {
                'promo_id': p.id,
                'item_id': p.item_id,
                'promo_price': int(p.discounted_price() or p.item.item_price),
            }

    context = {
        'categories': categories,
        'items': items,
        # JSON object keyed by item_id, e.g. { "12": {promo_id: 3, promo_price: 900} }
        'promotions_map_json': json.dumps({str(k): v for k, v in promos_map.items()}),
        'search_query': search_query,
    }
    return render(request, 'POS.html', context)

# views.py
import json
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q

from .models import (
    Item, Cart, CartProduct,
    PromotionItem
)
from .views import consume_fifo  # if it's in views.py, else import from its module

@method_decorator(login_required, name='dispatch')
class SaveOrderView(View):
    def post(self, request):
        # POS မှာ JSON body ပို့နေတဲ့အတွက် JSON parse လုပ်ပါ
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

        items = payload.get('cart') or payload.get('items') or []
        payment_method = (payload.get('payment_method') or '').strip()
        customer_name = (payload.get('customer_name') or '').strip()

        if not items:
            return JsonResponse({'error': 'Cart is empty.'}, status=400)

        try:
            with transaction.atomic():
                cart = Cart.objects.create(
                    user=request.user,
                    customer_name=customer_name,
                    payment_method=payment_method,
                    source='pos'
                )

                for row in items:
                    item_id = row.get('id')
                    qty = int(row.get('quantity') or 0)
                    if not item_id or qty <= 0:
                        continue

                    product = get_object_or_404(Item, id=item_id)

                    # Frontend ကနေ လာနိုင်မယ့် flags
                    is_promo = bool(row.get('isPromo') or row.get('is_promo') or row.get('promo_id'))
                    promo_obj = None

                    if is_promo:
                        promo_id = row.get('promo_id')
                        promo_obj = get_object_or_404(PromotionItem, id=promo_id, status='active')

                        # ရရှိနိုင်တဲ့ promotion quantity စစ်ဆေး
                        if qty > promo_obj.quantity:
                            return JsonResponse(
                                {'error': f"Promotion for {product.item_name} has only {promo_obj.quantity} left."},
                                status=400
                            )
                        unit_price = int(promo_obj.discounted_price() or product.item_price)
                    else:
                        # frontend ထဲက unit price (promo မဟုတ်ရင် product price)
                        unit_price = int(row.get('unit_price') or row.get('price') or product.item_price)

                    # CartProduct
                    CartProduct.objects.create(
                        cart=cart,
                        item=product,
                        qty=qty,
                        unit_price=unit_price,
                        price=qty * unit_price
                    )

                    # FIFO stock consumption (exp date အနီးဆုံး မှစတင်ရောင်း)
                    note = f"POS {payment_method or ''}: "
                    if is_promo:
                        consume_fifo(
                            item=product, qty=qty,
                            sale_item=None,
                            use_promo=True, promotion=promo_obj,
                            note_prefix=note
                        )
                    else:
                        consume_fifo(
                            item=product, qty=qty,
                            sale_item=None,
                            use_promo=False,
                            note_prefix=note
                        )

                cart.update_total_amount()
                tax_amount = cart.tax_amount
                grand_total = cart.total_with_tax

            return JsonResponse({
                'ok': True,
                'cart_id': cart.id,
                'subtotal': cart.total_amount,
                'tax': tax_amount,
                'total': grand_total
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)        
                  
@login_required
def print_preview(request):
    cart = Cart.objects.filter(user=request.user).order_by('-id').first()
    items = CartProduct.objects.filter(cart=cart)
    tax_amount = cart.tax_amount if cart else 0
    grand_total = cart.total_with_tax if cart else 0

    return render(request, 'print_invoice.html', {
        'cart': cart,
        'items': items,
        'tax_amount': tax_amount,
        'grand_total': grand_total,
    })

    

def search_customer(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        profiles = customerpos.objects.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        )[:5]

        for profile in profiles:
            results.append({
                'name': profile.name,
                'phone': profile.phone or '',
            })

    return JsonResponse(results, safe=False)


@login_required
def purchaseorder_view(request):
    if request.user.userprofile.role != 'pharmacist':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('login')

    supplier_list = Supplier.objects.all().order_by('supplier_name')
    paginator = Paginator(supplier_list, 10)
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)

    return render(request, 'purchaseorder.html', {'suppliers': suppliers})


@login_required
def create_or_update_supplier(request):
    if request.method == 'POST':
        try:
            supplier_id = request.POST.get('supplier_id')

            if supplier_id:  # Update
                supplier = get_object_or_404(Supplier, pk=supplier_id)
                supplier.supplier_name = request.POST.get('supplier_name')
                supplier.company = request.POST.get('company')
                supplier.contact_person = request.POST.get('contact_person')
                supplier.email = request.POST.get('email')
                supplier.phone = request.POST.get('phone')
                supplier.address = request.POST.get('address')
                supplier.status = request.POST.get('status') == 'active'
                supplier.save()
                messages.success(request, "✅Supplier updated successfully.")
            else:  # Create
                Supplier.objects.create(
                    supplier_name=request.POST.get('supplier_name'),
                    company=request.POST.get('company'),
                    contact_person=request.POST.get('contact_person'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    address=request.POST.get('address'),
                    status=request.POST.get('status') == 'active'
                )
                messages.success(request, "✅Supplier created successfully.")

            return redirect('purchaseorder_view')

        except Exception as e:
            messages.error(request, f"❌Error: {str(e)}")
            return redirect('purchaseorder_view')

    return redirect('purchaseorder_view')


@login_required
def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        try:

            supplier.delete()
            messages.success(request, "✅Supplier deleted successfully.")
        except Exception as e:
            messages.error(request, f"❌Error: {str(e)}")

    return redirect('purchaseorder_view')


@require_POST
@login_required
def increase_cp_qty(request, cp_id):
    cp = get_object_or_404(CartProduct, id=cp_id, cart__user=request.user)
    promo = _get_promo_for_cp(request, cp)

    if promo and cp.qty + 1 > promo.quantity:
        messages.warning(request, f"Only {promo.quantity} available at promo price.")
        return redirect("medicine_list")
    if not promo and cp.qty + 1 > cp.item.item_quantity:
        messages.warning(request, f"Only {cp.item.item_quantity} left in stock.")
        return redirect("medicine_list")

    cp.qty = F("qty") + 1
    cp.save(update_fields=["qty"])
    cp.refresh_from_db(fields=["qty"])
    cp.price = cp.qty * cp.unit_price
    cp.save(update_fields=["price"])
    cp.cart.update_total_amount()
    return redirect("medicine_list")


@require_POST
@login_required
def decrease_cp_qty(request, cp_id):
    cp = get_object_or_404(CartProduct, id=cp_id, cart__user=request.user)
    if cp.qty > 1:
        cp.qty = F("qty") - 1
        cp.save(update_fields=["qty"])
        cp.refresh_from_db(fields=["qty"])
        cp.price = cp.qty * cp.unit_price
        cp.save(update_fields=["price"])
    else:
        _remove_cp_and_session(request, cp)
    if Cart.objects.filter(id=getattr(cp.cart, "id", None)).exists():
        cp.cart.update_total_amount()
    return redirect("medicine_list")

@require_POST
@login_required
def remove_cp(request, cp_id):
    cp = get_object_or_404(CartProduct, id=cp_id, cart__user=request.user)
    cart = cp.cart
    _remove_cp_and_session(request, cp)
    if Cart.objects.filter(id=getattr(cart, "id", None)).exists():
        cart.update_total_amount()
    return redirect("medicine_list")

@require_POST
@login_required
def update_cp_qty(request, cp_id):
    cp = get_object_or_404(CartProduct, id=cp_id, cart__user=request.user)
    try:
        qty = int(request.POST.get("quantity", cp.qty))
    except ValueError:
        qty = cp.qty

    if qty <= 0:
        _remove_cp_and_session(request, cp)
        if Cart.objects.filter(id=getattr(cp.cart, "id", None)).exists():
            cp.cart.update_total_amount()
        return redirect("medicine_list")

    promo = _get_promo_for_cp(request, cp)
    if promo and qty > promo.quantity:
        messages.warning(request, f"Only {promo.quantity} available at promo price.")
        return redirect("medicine_list")
    if not promo and qty > cp.item.item_quantity:
        messages.warning(request, f"Only {cp.item.item_quantity} left in stock.")
        return redirect("medicine_list")





def medicine_list(request):
    active_tab = request.session.pop('active_tab', 'products-tab')
    user = request.user
    categories = Category.objects.all()

    cid = request.GET.get('cid')
    search_query = request.GET.get('search', '')

    items = Item.objects.all().order_by('-id')

    if cid:
        items = items.filter(category_id=cid)

    if search_query:
        items = items.filter(item_name__icontains=search_query)

    # ✅ Pagination
    paginator = Paginator(items, 8)
    page_number = request.GET.get('page')
    items = paginator.get_page(page_number)

    # ✅ Only customers
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'customer':
        messages.error(request, "Dear customer, you need register to encourage purchases.")
        return render(request, 'medicine_list.html', {
            'categories': categories,
            'items': items
        })

    cart, created = Cart.objects.get_or_create(user=user, defaults={'created_date': timezone.now()})
    cart_products = CartProduct.objects.filter(cart=cart)

    cart.update_total_amount()
    cart.refresh_from_db()
    subtotal = cart.total_amount

    # 🆕 2% TAX + shipping
    tax_amount = compute_tax(subtotal)
    grand_total = subtotal + SHIPPING_FEE + tax_amount

    # ✅ Checkout
    if request.method == 'POST' and 'place_order' in request.POST:
        if not cart_products.exists():
            messages.warning(request, "Your cart is empty.")
            return redirect('medicine_list')

        sale = Sale.objects.create(
            invoice_no=f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            user=user,
            total_amount=subtotal,      # items only
            final_amount=grand_total,   # items + 2% tax + shipping
        )

    # ✅ promotion mapping (if you use promo_cart in session)
        promo_cart = request.session.get("promo_cart", {})
        for cp in cart_products:
            promo_id = promo_cart.get(str(cp.id))
            promotion = None
            is_promotion = False
            if promo_id:
                try:
                    promotion = PromotionItem.objects.get(id=promo_id, status="active")
                    is_promotion = True
                except PromotionItem.DoesNotExist:
                    pass

            # price ကို unit_price သာသိမ်း (line total မဟုတ်)
            SaleItem.objects.create(
                sale=sale,
                item=cp.item,
                quantity=cp.qty,
                price=cp.unit_price,
                promotion=promotion if is_promotion else None,
                is_promotion=is_promotion,
            )

                # clear cart + session
        cart_products.delete()
        cart.total_amount = 0
        cart.save()
        if "promo_cart" in request.session:
            del request.session["promo_cart"]

        messages.success(request, "✅ Checkout completed successfully.")
        # success render (tax/total ပြန်ထုတ်ချင်ရင် context ထည့်ပေး)
        return render(request, 'medicine_list.html', {
            'items': items,
            'categories': categories,
            'cart': cart,
            'cart_products': [],
            'checkout_success': True,
            'sale': sale,
            'tax_amount': tax_amount,
            'grand_total': grand_total,
            'search_query': search_query,
        })

    # GET render
    return render(request, 'medicine_list.html', {
        'items': items,
        'categories': categories,
        'cart': cart,
        'cart_products': cart_products,
        'tax_amount': tax_amount,      
        'grand_total': grand_total,    
        'search_query': search_query,
    })


@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    if item.item_quantity <= 0:
        messages.error(request, f"{item.item_name} is out of stock.")
        return redirect('medicine_list')

    cp, _ = CartProduct.objects.get_or_create(
        cart=cart, item=item, unit_price=item.item_price,
        defaults={'qty': 0, 'price': 0}
    )
    cp.qty += 1
    cp.price = cp.qty * cp.unit_price
    cp.save(update_fields=['qty','price'])

    cart.update_total_amount()
    return redirect('medicine_list')


import re
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

@login_required
def place_order_view(request):
    user = request.user
    name = request.GET.get("name")
    phone = request.GET.get("phone")
    address = request.GET.get("address")

    # ✅ Phone validation (11 digits only)
    if not re.fullmatch(r'\d{11}', phone or ""):
        messages.error(request, "Phone number must be exactly 11 digits (numbers only).")
        return redirect("medicine_list")

    # ✅ Role check
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'customer':
        messages.error(request, "Only customers can place an order.")
        return redirect("base")

    try:
        cart = get_object_or_404(Cart, user=user)
        cart_items = CartProduct.objects.filter(cart=cart)
        if not cart_items.exists():
            messages.warning(request, "Your cart is empty.")
            return redirect("medicine_list")

        # Subtotal + tax + shipping
        cart.update_total_amount()
        subtotal = cart.total_amount
        tax_amount = compute_tax(subtotal)         # 🆕 2%
        grand_total = subtotal + SHIPPING_FEE + tax_amount

        # Create sale
        sale = Sale.objects.create(
            invoice_no=f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            user=user,
            name=name,
            phone=phone,
            address=address,
            total_amount=subtotal,      # items only
            final_amount=grand_total,   # items + tax + shipping
        )

        # Handle promotions
        promo_cart = request.session.get("promo_cart", {})
        for cp in cart_items:
            promo_id = promo_cart.get(str(cp.id))
            promotion = None
            is_promotion = False
            if promo_id:
                try:
                    promotion = PromotionItem.objects.get(id=promo_id, status="active")
                    is_promotion = True
                except PromotionItem.DoesNotExist:
                    pass

            SaleItem.objects.create(
                sale=sale,
                item=cp.item,
                quantity=cp.qty,
                price=cp.unit_price,  # unit price (promo included)
                promotion=promotion if is_promotion else None,
                is_promotion=is_promotion,
            )

        # Clear cart & promo session
        cart_items.delete()
        cart.total_amount = 0
        cart.save()
        if "promo_cart" in request.session:
            del request.session["promo_cart"]

        messages.success(request, "Order placed successfully!")
        return redirect("medicine_list")

    except Cart.DoesNotExist:
        messages.error(request, "No active cart found.")
        return redirect("medicine_list")
    

@login_required
def customer_profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, "Profile not found.")
        return redirect('customer_dashboard')

    return render(request, 'customer/profile.html', {
        'profile': profile
    })

@login_required
def edit_profile(request):
    user = request.user
    profile = user.userprofile

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        profile.gender = request.POST.get('gender')
        profile.date_of_birth = request.POST.get('date_of_birth')

        user.save()
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('customer_profilereal')

@login_required
def customer_profile_view(request):
    user = request.user

    # ✅ Role check
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'customer':
        messages.error(request, "Only customers can access this page.")
        return redirect('base')

    # ✅ Get purchase history with final amount
    sales = Sale.objects.filter(user=user, status='confirmed').order_by('-created_date')

    # စုစုပေါင်းအသုံးစရိတ် (ခေါင်းစဉ်ပြချင်လို့)
    total_spent = sales.aggregate(
        spent=Coalesce(Sum('final_amount'), 0)
    )['spent']

    return render(request, 'customer_profile.html', {
        'sales': sales,
        'total_spent': total_spent
    })


# @login_required
# @csrf_exempt
# def chatbot_view(request):
#     if request.method == 'POST':
#         question = request.POST.get('message', '')
#         print(f"User asked: {question}")


#     client = genai.Client(api_key="AIzaSyAuE0XYFF61K9Po0sJlLDfgvZn6XDVu3D4")

#     response = client.models.generate_content(
#         model="gemini-2.5-flash",
#         contents={question} ,
#     )

#     # print(response.text)


#     return JsonResponse({'reply': response.text })

# views.py (update)
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
# import your genai client as before

@require_POST
@csrf_protect
def chatbot_view(request):
    # 1) user auth check (don't redirect)
    if not request.user.is_authenticated:
        return JsonResponse({
            'reply': "You need to register or login first.",
            'type': 'system',
            'code': 'unauthenticated'
        })

    # 2) get message
    question = request.POST.get('message', '').strip()
    if not question:
        return JsonResponse({
            'reply': "Please enter a question.",
            'type': 'system',
            'code': 'empty'
        })

    # 3) call your AI client (keep same as before)
    try:
        client = genai.Client(api_key="AIzaSyAuE0XYFF61K9Po0sJlLDfgvZn6XDVu3D4")  # your key
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents={question},
        )
        print(response.text)
        text = getattr(response, 'text', '') or str(response)
        
    except Exception as e:
        # handle errors gracefully
        text = "Sorry, something went wrong. Please try again later."

    return JsonResponse({
        'reply': text,
        'type': 'bot',
        'code': 'ok'
    })