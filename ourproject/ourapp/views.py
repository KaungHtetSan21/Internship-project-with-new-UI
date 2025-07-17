






from django.contrib.auth.models import User

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from django.contrib.auth import authenticate, login
from .forms import CustomerRegisterForm
from .models import UserProfile
from django.db.models import Sum
from google import genai





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
            pass  # Profile မရှိသေးဆိုလည်း form တင်ပေးမယ်

    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            # ✅ User create
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # ✅ UserProfile already exists check
            if not UserProfile.objects.filter(user=user).exists():
                UserProfile.objects.create(
                    user=user,
                    role='customer',
                    phone=form.cleaned_data['phone'],
                    address=form.cleaned_data.get('address'),
                    gender=form.cleaned_data.get('gender'),
                    date_of_birth=form.cleaned_data.get('date_of_birth')
                )
            else:
                messages.warning(request, "UserProfile already exists for this user.")

            # ✅ Login
            login(request, user)
            messages.success(request, "Account created and logged in successfully.")
            return redirect('customer_dashboard')
        else:
            messages.error(request, "Form is invalid. Please check your inputs.")
    else:
        form = CustomerRegisterForm()

    return render(request, 'register.html', {'form': form})

# from django.views.decorators.csrf import csrf_exempt
# from django.contrib.auth.models import User
# from django.http import JsonResponse

# import json

# @csrf_exempt
# def register_customer_ajax(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)

#             username = data.get('username', '').strip().lower()
#             password = data.get('password')
#             phone = data.get('phone')

#             # ✅ Check if username already exists
#             user = User.objects.filter(username=username).first()

#             if user:
#                 if UserProfile.objects.filter(user=user).exists():
#                     return JsonResponse({'error': 'UserProfile already exists for this user'}, status=400)
#             else:
#                 user = User.objects.create_user(username=username, password=password)

#             # ✅ Double-check again
#             if UserProfile.objects.filter(user=user).exists():
#                 return JsonResponse({'error': 'Profile already exists'}, status=400)

#             UserProfile.objects.create(user=user, role='customer', phone=phone)

#             return JsonResponse({'message': 'Customer registered successfully'})

#         except Exception as e:
#             return JsonResponse({'error': f'Exception: {str(e)}'}, status=500)

#     return JsonResponse({'error': 'Invalid request'}, status=400)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import UserProfile
import json

# @csrf_exempt
# def register_customer_ajax(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)

#             username = data.get('username', '').strip()
#             password = data.get('password')
#             phone = data.get('phone')

#             print("Phone received:", phone)

#             # ✅ Step 1: Check if username already exists
#             if User.objects.filter(username=username).exists():
#                 return JsonResponse({'error': 'Username already exists'}, status=400)

#             # ✅ Step 2: Create new user
#             user = User.objects.create_user(username=username, password=password)

#             # ✅ Step 3: Double-check if profile already exists for this user
#             if UserProfile.objects.filter(user=user).exists():
#                 return JsonResponse({'error': 'UserProfile already exists for this user'}, status=400)

#             # ✅ Step 4: Create the UserProfile
#             UserProfile.objects.create(user=user, role='customer', phone=phone)

#             return JsonResponse({'message': 'Customer registered successfully'})

#         except Exception as e:
#             return JsonResponse({'error': f'Exception: {str(e)}'}, status=500)

#     return JsonResponse({'error': 'Invalid request'}, status=400)


from .models import customerpos
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

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




from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

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
# views.py
from django.contrib.auth import logout
from django.contrib import messages

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render


from datetime import date, timedelta




# views.py
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required



    

# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    if request.user.userprofile.role != 'admin':
        return HttpResponseForbidden("Admins only.")
    return render(request, 'admin/dashboard.html')






from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from .models import Sale, SaleItem, Item
import datetime

@login_required
def pharmacist_dashboard_view(request):
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden("Unauthorized")

    # ✅ Total Orders
    total_orders = Sale.objects.count()

    # ✅ Low Stock
    low_stock_count = Item.objects.filter(item_quantity__lt=10).count()
    low_stock_items = Item.objects.filter(item_quantity__lt=10).order_by('item_quantity')

    # ✅ Expiring Items
    today = datetime.date.today()
    expiring_items = Item.objects.filter(exp_date__lte=today + datetime.timedelta(days=90)).order_by('exp_date')

    # ✅ All Online Orders (instead of just 5)
    online_orders_list = (
        Sale.objects
        .exclude(user__userprofile__role='pharmacist')
        .select_related('user')
        .order_by('-created_date')
    )

    # ✅ POS Orders (from Cart)
    pos_orders = Cart.objects.filter(payment_method__in=['cash', 'mobile', 'print'])
    pos_total = pos_orders.count()
    pos_revenue = pos_orders.aggregate(total=Coalesce(Sum('total_amount'), 0))['total']

    # ✅ Online Orders Summary
    online_total = online_orders_list.count()
    online_revenue = online_orders_list.aggregate(total=Coalesce(Sum('total_amount'), 0))['total']

    # ✅ Dashboard Stats
    dashboard_stats = [
        {
            'label': 'Total Orders',
            'icon': 'fa-prescription-bottle-alt',
            'bg': 'bg-blue-100',
            'text': 'text-blue-600',
            'value': total_orders
        },
        {
            'label': 'POS Orders',
            'icon': 'fa-cash-register',
            'bg': 'bg-green-100',
            'text': 'text-green-600',
            'value': pos_total
        },
        {
            'label': 'Online Orders',
            'icon': 'fa-globe',
            'bg': 'bg-purple-100',
            'text': 'text-purple-600',
            'value': online_total
        },
        {
            'label': 'POS Revenue',
            'icon': 'fa-dollar-sign',
            'bg': 'bg-green-100',
            'text': 'text-green-600',
            'value': f"{pos_revenue} Ks"
        },
        {
            'label': 'Online Revenue',
            'icon': 'fa-credit-card',
            'bg': 'bg-yellow-100',
            'text': 'text-yellow-600',
            'value': f"{online_revenue} Ks"
        },
        {
            'label': 'Low Stock Items',
            'icon': 'fa-exclamation-triangle',
            'bg': 'bg-red-100',
            'text': 'text-red-600',
            'value': low_stock_count
        },
    ]

    context = {
        'dashboard_stats': dashboard_stats,
        'low_stock_items': low_stock_items,
        'expiring_items': expiring_items,
        'online_orders_list': online_orders_list,  # ✅ context key changed
    }

    return render(request, 'pharmacist/dashboard.html', context)

@login_required
def confirm_order_view(request, order_id):
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden()
    try:
        order = Sale.objects.get(id=order_id)
        order.status = 'confirmed'
        order.save()
        Notification.objects.create(
        recipient=order.user,
        message=f"Your order {order.invoice_no} has been confirmed by the pharmacist."
    )

        messages.success(request, "Order confirmed successfully.")
    except Sale.DoesNotExist:
        messages.error(request, "Order not found.")
    return redirect('pharmacist_dashboard')

@login_required
def cancel_order_view(request, order_id):
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden()
    try:
        order = Sale.objects.get(id=order_id)
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
def mark_notification_read(request, noti_id):
    notification = get_object_or_404(Notification, id=noti_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('customer_dashboard')  # or your desired page


@login_required
def customer_dashboard_view(request):
    user = request.user

    cart = Cart.objects.filter(user=user).last()
    cart_products = CartProduct.objects.filter(cart=cart) if cart else []

    total_orders = Sale.objects.filter(user=user).count()
    total_items = SaleItem.objects.filter(sale__user=user).aggregate(total=Coalesce(Sum('quantity'), 0))['total']
    total_spent = Sale.objects.filter(user=user).aggregate(spent=Coalesce(Sum('total_amount'), 0))['spent']

    dashboard_stats = [
        {
            'label': 'Total Orders',
            'icon': 'fa-box',
            'color': 'primary',
            'value': total_orders
        },
        {
            'label': 'Items Purchased',
            'icon': 'fa-shopping-basket',
            'color': 'success',
            'value': total_items
        },
        {
            'label': 'Total Spent',
            'icon': 'fa-dollar-sign',
            'color': 'warning',
            'value': f"{total_spent} Ks"
        },
    ]
    notifications = Notification.objects.filter(
        recipient=user
    ).order_by('-created_at')  # newest first
    context = {
        'dashboard_stats': dashboard_stats,
        'cart': cart,
        'cart_products': cart_products,
        'notifications': notifications,
        # any other context data needed
    }
    return render(request, 'customer/dashboard.html', context)









from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from .models import Sale, SaleItem, Cart, CartProduct


# ✅ All your existing views remain same (register, login, logout, dashboards...)
from django.db.models import Sum, Count, F, FloatField, ExpressionWrapper
from django.db.models.functions import Coalesce


@login_required
def report_view(request):
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden("Pharmacists only.")

    # ✅ All Sales (POS + Online)
    total_transactions = Cart.objects.count() + Sale.objects.exclude(user__userprofile__role='pharmacist').count()
    total_revenue = (
        (Cart.objects.aggregate(total=Coalesce(Sum('total_amount'), 0))['total']) +
        (Sale.objects.exclude(user__userprofile__role='pharmacist').aggregate(total=Coalesce(Sum('total_amount'), 0))['total'])
    )

    # ✅ Items Sold (POS only for now)
    items_sold = CartProduct.objects.aggregate(total_qty=Coalesce(Sum('qty'), 0))['total_qty']

    # ✅ Avg Margin (POS only)
    cart_products = CartProduct.objects.annotate(
        margin=ExpressionWrapper(
            (F('price') - F('item__purcharse_price')) / F('item__purcharse_price') * 100,
            output_field=FloatField()
        )
    )
    avg_margin = round(cart_products.aggregate(avg=Coalesce(Sum('margin') / Count('id'), 0.0))['avg'], 2)

    # ✅ POS Summary + Full Order List
    pos_orders = Cart.objects.filter(payment_method__in=['cash', 'mobile', 'print']).order_by('-created_date')
    pos_transactions = pos_orders.count()
    pos_revenue = pos_orders.aggregate(total=Coalesce(Sum('total_amount'), 0))['total']
    for order in pos_orders:
        if not order.customer_name:
            order.customer_name = "Walking Customer"

    # ✅ Online Summary + Full Order List
    online_orders = Sale.objects.exclude(user__userprofile__role='pharmacist').order_by('-created_date')
    online_transactions = online_orders.count()
    online_revenue = online_orders.aggregate(total=Coalesce(Sum('total_amount'), 0))['total']
    for order in online_orders:
        if not order.name:
            order.name = order.user.username

    # ✅ Top Selling Products (POS)
    top_products = (
        CartProduct.objects
        .values('item_id', 'item__item_name', 'item__category__name')
        .annotate(total_qty=Sum('qty'), total_revenue=Sum('price'))
        .order_by('-total_qty')[:5]
    )
    for product in top_products:
        try:
            item = Item.objects.get(id=product['item_id'])
            cost = item.purcharse_price or 1
            sell = product['total_revenue']
            qty = product['total_qty']
            avg_sell = sell / qty if qty else 0
            margin = ((avg_sell - cost) / cost) * 100
            product['margin'] = round(margin, 2)
        except:
            product['margin'] = "-"

    # ✅ Summary Card for Sales Report Tab
    summary_list = [
        {
            'label': 'POS Transactions',
            'icon': 'fa-receipt',
            'bg': 'bg-blue-100',
            'text': 'text-blue-600',
            'value': pos_transactions,
            'unit': '',
        },
        {
            'label': 'Online Transactions',
            'icon': 'fa-receipt',
            'bg': 'bg-blue-100',
            'text': 'text-blue-600',
            'value': online_transactions,
            'unit': '',
        },
        {
            'label': 'POS Revenue',
            'icon': 'fa-dollar-sign',
            'bg': 'bg-green-100',
            'text': 'text-green-600',
            'value': pos_revenue,
            'unit': 'Ks',
        },
        {
            'label': 'Online Revenue',
            'icon': 'fa-dollar-sign',
            'bg': 'bg-green-100',
            'text': 'text-green-600',
            'value': online_revenue,
            'unit': 'Ks',
        },
        {
            'label': 'Items Sold',
            'icon': 'fa-shopping-basket',
            'bg': 'bg-purple-100',
            'text': 'text-purple-600',
            'value': items_sold,
            'unit': '',
        },
        {
            'label': 'Avg. Margin',
            'icon': 'fa-percentage',
            'bg': 'bg-yellow-100',
            'text': 'text-yellow-600',
            'value': avg_margin,
            'unit': '%',
        },
    ]

    return render(request, 'report.html', {
            # ✅ Sales Report Tab Data
            'summary_list': summary_list,
            'top_products': top_products,

            # ✅ POS Report Tab Data
            'pos_orders_list': pos_orders,
            'pos_transactions': pos_transactions,
            'pos_revenue': pos_revenue,

            # ✅ Online Report Tab Data
            'online_orders_list': online_orders,
            'online_transactions': online_transactions,
            'online_revenue': online_revenue,

            # ✅ Global Totals (if you need at top header)
            'total_transactions': total_transactions,
            'total_revenue': total_revenue,
            'items_sold': items_sold,
            'avg_margin': avg_margin,
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
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from .models import Item, Category, Supplier

@login_required
def inventory_view(request):
    if request.user.userprofile.role != 'pharmacist':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('login')

    items = Item.objects.all().order_by('-id')
    for item in items:
        if item.exp_date:
            item.days_left = (item.exp_date - date.today()).days
        else:
            item.days_left = None
    categories = Category.objects.all()

    # ---------------------- CATEGORY CREATE ----------------------
    if request.method == 'POST' and 'save_category' in request.POST:
        name = request.POST.get('category_name')
        description = request.POST.get('category_description', '')
        if name:
            Category.objects.create(name=name, description=description)
            messages.success(request, "Category added successfully.")
        else:
            messages.error(request, "Category name is required.")
        return redirect('inventory_view')

    # ---------------------- ITEM CREATE OR EDIT ----------------------
    if request.method == 'POST' and 'save_item' in request.POST:
        item_id = request.POST.get('item_id')
        is_edit = bool(item_id)

        try:
            category = Category.objects.get(id=request.POST.get('category'))
        except Category.DoesNotExist:
            messages.error(request, "Invalid category.")
            return redirect('inventory_view')

        # Prepare cleaned data
        data = {
            'category': category,
            'item_name': request.POST.get('item_name'),
            'item_quantity': request.POST.get('item_quantity') or 0,
            'item_price': request.POST.get('item_price') or 0,
            'purcharse_price': request.POST.get('purcharse_price') or 0,
            'item_description': request.POST.get('item_description') or '',
            'exp_date': parse_date(request.POST.get('exp_date')),
            'brand_name': request.POST.get('brand_name') or '',
            'batch_number': request.POST.get('batch_number') or '',
            'stock_minimum': request.POST.get('stock_minimum') or 10,
            'is_limited': 'is_limited' in request.POST,
            'max_quantity': request.POST.get('max_quantity') or 5,
        }

        # Get image from FILES
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

    # ---------------------- ITEM DELETE ----------------------
    if request.method == 'POST' and 'delete_item' in request.POST:
        item_id = request.POST.get('delete_item')
        item = get_object_or_404(Item, id=item_id)
        item.delete()
        messages.success(request, "Item deleted successfully.")
        return redirect('inventory_view')

    # ---------------------- RENDER PAGE ----------------------
    return render(request, 'inventory.html', {
        'items': items,
        'categories': categories,
    })

from django.views.decorators.http import require_POST

@require_POST
@login_required
def send_to_promotion(request):
    if request.user.userprofile.role != 'pharmacist':
        messages.error(request, "Unauthorized.")
        return redirect('inventory_view')

    item_id = request.POST.get('item_id')
    item = get_object_or_404(Item, id=item_id)

    # Example: Mark item as promotion or move to another model/table if needed
    item.is_promotion = True
    item.save()

    messages.success(request, f"{item.item_name} has been moved to promotion area.")
    return redirect('inventory_view')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ourapp.models import *
from .models import *
from django.utils import timezone
@login_required
def order_view(request):
    if request.user.userprofile.role != 'pharmacist':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('pharmacist_dashboard')

    category_id = request.GET.get('cid')
    categories = Category.objects.all()
    if category_id:
        items = Item.objects.filter(category_id=category_id).order_by('-id') 
    else:
        items = Item.objects.all().order_by('-id') 
  
    context = {
        'categories': categories,
        'items': items,
    }
    return render(request, 'POS.html', context)

from django.views import View  # ✅ OK
from django.http import JsonResponse
from .models import Cart, CartProduct, Item, StockHistory, Possalesreport, Sale, SaleItem
import json

# views.py
class SaveOrderView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body)
            items = payload.get('cart', [])
            customer_name = payload.get('customer_name', '')
            payment_method = payload.get('payment_method', '')  # ✅ GET payment type

            # ✅ Create cart with payment_method
            cart = Cart.objects.create(
                user=request.user,
                total_amount=0,
                customer_name=customer_name,
                payment_method=payment_method  # ✅ Save to model
            )

            total = 0
            for item in items:
                product_id = int(item['id'])
                quantity = int(item['quantity'])
                price = float(item['price'])

                product = Item.objects.get(id=product_id)
                amount = quantity * price

                CartProduct.objects.create(
                    cart=cart,
                    item=product,
                    qty=quantity,
                    price=price
                )

                # ✅ Update stock
                product.item_quantity -= quantity
                product.save()

                # ✅ StockHistory log
                StockHistory.objects.create(
                    item=product,
                    action='out',
                    quantity=quantity,
                    note=f"POS sale to {customer_name or 'Walk-in'}"
                )

                # ✅ Sale Report Log
                Possalesreport.objects.create(
                    item=product,
                    user=request.user,
                    quantity=quantity,
                    price=price,
                    amount=amount
                )

                total += amount

            cart.total_amount = total
            cart.save()

            return JsonResponse({'message': 'Order saved successfully!'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500) 
                  
@login_required
def print_preview(request):
    cart = Cart.objects.filter(user=request.user).order_by('-id').first()
    items = CartProduct.objects.filter(cart=cart)
    return render(request, 'print_invoice.html', {
        'cart': cart,
        'items': items
    })
    





from django.db.models import Q
from django.http import JsonResponse

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

    



# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages
# from .models import Supplier

# def purchaseorder_view(request):
#     suppliers = Supplier.objects.all()
#     return render(request, 'purchaseorder.html', {'suppliers': suppliers})

# def create_supplier(request):
#     if request.method == 'POST':
#         Supplier.objects.create(
#             supplier_name=request.POST.get('supplier_name'),
#             company=request.POST.get('company'),
#             contact_person=request.POST.get('contact_person'),
#             email=request.POST.get('email'),
#             phone=request.POST.get('phone'),
#             address=request.POST.get('address'),
#             status=request.POST.get('status') == 'active'
#         )
#         messages.success(request, "Supplier created successfully.")
#         return redirect('purchaseorder_view')

# def edit_supplier(request, pk):
#     supplier = get_object_or_404(Supplier, pk=pk)
#     if request.method == 'POST':
#         supplier.supplier_name = request.POST.get('supplier_name')
#         supplier.company = request.POST.get('company')
#         supplier.contact_person = request.POST.get('contact_person')
#         supplier.email = request.POST.get('email')
#         supplier.phone = request.POST.get('phone')
#         supplier.address = request.POST.get('address')
#         supplier.status = request.POST.get('status') == 'active'
#         supplier.save()
#         messages.success(request, "Supplier updated successfully.")
#         return redirect('purchaseorder_view')
#     return render(request, 'edit_supplier.html', {'supplier': supplier})

# def delete_supplier(request, pk):
#     supplier = get_object_or_404(Supplier, pk=pk)
#     if request.method == 'POST':
#         supplier.delete()
#         messages.success(request, "Supplier deleted successfully.")
#         return redirect('purchaseorder_view')
#     return render(request, 'confirm_delete.html', {'supplier': supplier})


from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Supplier

def purchaseorder_view(request):
    # Get all suppliers ordered by name and paginate them
    supplier_list = Supplier.objects.all().order_by('supplier_name')
    paginator = Paginator(supplier_list, 10)  # Show 10 suppliers per page
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)
    
    return render(request, 'purchaseorder.html', {'suppliers': suppliers})

def create_supplier(request):
    if request.method == 'POST':
        try:
            supplier_id = request.POST.get('supplier_id')
            
            if supplier_id:  # Update existing supplier
                supplier = get_object_or_404(Supplier, pk=supplier_id)
                supplier.name = request.POST.get('name')
                supplier.company = request.POST.get('company')
                supplier.contact_person = request.POST.get('contact_person')
                supplier.email = request.POST.get('email')
                supplier.phone = request.POST.get('phone')
                supplier.address = request.POST.get('address')
                supplier.is_active = request.POST.get('status') == 'active'
                supplier.save()
                messages.success(request, "Supplier updated successfully.")
            else:  # Create new supplier
                Supplier.objects.create(
                    name=request.POST.get('name'),
                    company=request.POST.get('company'),
                    contact_person=request.POST.get('contact_person'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    address=request.POST.get('address'),
                    is_active=request.POST.get('status') == 'active'
                )
                messages.success(request, "Supplier created successfully.")
            
            return redirect('purchaseorder_view')
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('purchaseorder_view')

    # If not POST, show the form
    return redirect('purchaseorder_view')

def edit_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        try:
            supplier.name = request.POST.get('name')
            supplier.company = request.POST.get('company')
            supplier.contact_person = request.POST.get('contact_person')
            supplier.email = request.POST.get('email')
            supplier.phone = request.POST.get('phone')
            supplier.address = request.POST.get('address')
            supplier.is_active = request.POST.get('status') == 'active'
            supplier.save()
            
            messages.success(request, "Supplier updated successfully.")
            return redirect('purchaseorder_view')
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('purchaseorder_view')

    # If not POST, show the form
    return redirect('purchaseorder_view')

def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        try:
            supplier.delete()
            messages.success(request, "Supplier deleted successfully.")  
            return redirect('purchaseorder_view')
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('purchaseorder_view')

    # If not POST, show the confirmation
    return redirect('purchaseorder_view')

@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_product, created = CartProduct.objects.get_or_create(
        cart=cart,
        item=item,
        defaults={'qty': 0, 'price': 0}
    )

    if item.is_limited and (cart_product.qty + 1 > item.max_quantity):
        messages.warning(request, f"{item.item_name} သည် {item.max_quantity} ခုထက် များ၍မရပါ။")
        return redirect('medicine_list')

    cart_product.qty += 1
    cart_product.price = cart_product.qty * item.item_price
    cart_product.save()

    cart.update_total_amount()
    cart.refresh_from_db()
    return redirect('medicine_list')


@login_required
def increase_quantity(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(Item, id=item_id)
    cart_product = get_object_or_404(CartProduct, cart=cart, item=item)

    if item.is_limited and cart_product.qty + 1 > item.max_quantity:
        messages.warning(request, f"{item.item_name} သည် {item.max_quantity} ထက် များလွန်းပါသည်။")
        return redirect('medicine_list')

    cart_product.qty += 1
    cart_product.price = cart_product.qty * item.item_price
    cart_product.save()

    cart.update_total_amount()
    cart.refresh_from_db()

    return redirect('medicine_list')


@login_required
def decrease_quantity(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(Item, id=item_id)
    cart_product = get_object_or_404(CartProduct, cart=cart, item=item)

    if cart_product.qty > 1:
        cart_product.qty -= 1
        cart_product.price = cart_product.qty * item.item_price
        cart_product.save()
    else:
        cart_product.delete()

    cart.update_total_amount()
    cart.refresh_from_db()
    return redirect('medicine_list')

@login_required
def remove_from_cart(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(Item, id=item_id)

    try:
        cart_product = CartProduct.objects.get(cart=cart, item=item)
        cart_product.delete()
        cart.update_total_amount()
    except CartProduct.DoesNotExist:
        pass

    return redirect('medicine_list')

from django.views.decorators.http import require_POST

@require_POST
@login_required
def update_quantity(request, item_id):
    user = request.user

    # ✅ Role Check (only customers)
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'customer':
        messages.error(request, "You do not have permission to update cart items.")
        return redirect('medicine_list')

    cart = get_object_or_404(Cart, user=user)
    item = get_object_or_404(Item, id=item_id)
    cart_product = get_object_or_404(CartProduct, cart=cart, item=item)

    try:
        qty = int(request.POST.get('quantity', 1))

        if item.is_limited and qty > item.max_quantity:
            messages.warning(request, f"{item.item_name} သည် {item.max_quantity} ခုထက် များ၍မရပါ။")
            return redirect('medicine_list')

        if qty > 0:
            cart_product.qty = qty
            cart_product.price = qty * item.item_price
            cart_product.save()
        else:
            cart_product.delete()  # 0 ဆိုရင်ဖျက်လိုက်မယ်

    except ValueError:
        messages.error(request, "Invalid quantity value.")

    cart.update_total_amount()
    cart.refresh_from_db()

    return redirect('medicine_list')


@login_required
def medicine_list(request):
    user = request.user

    # ✅ Only customers can access this page
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'customer':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('homeview')  # Or any fallback

    # ✅ Get or create cart
    cart, created = Cart.objects.get_or_create(user=user, defaults={'created_date': timezone.now()})
    cart_products = CartProduct.objects.filter(cart=cart)
    items = Item.objects.all().order_by('-id')

    # ✅ Refresh cart total
    cart.update_total_amount()  # Ensure this includes shipping and tax
    cart.refresh_from_db()

    # ✅ If POST, handle checkout (place order logic)
    if request.method == 'POST' and 'place_order' in request.POST:
        if not cart_products.exists():
            messages.warning(request, "Your cart is empty.")
            return redirect('medicine_list')

        # Calculate total with shipping and tax
        shipping_fee = 5.99
        tax = 1.00
        total_amount = cart.total_amount + shipping_fee + tax  # Final total with shipping and tax

        # Create sale
        sale = Sale.objects.create(
            invoice_no=f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            user=user,
            total_amount=total_amount  # Use the final total here
        )

        # Process cart items and update stock
        for cp in cart_products:
            cp.total_price = cp.qty * cp.item.item_price

            SaleItem.objects.create(
                sale=sale,
                item=cp.item,
                quantity=cp.qty,
                price=cp.price
            )
            cp.item.item_quantity -= cp.qty
            cp.item.save()

            StockHistory.objects.create(
                item=cp.item,
                action='out',
                quantity=cp.qty,
                note=f"Checked out by {user.username}"
            )

        # Clear the cart after checkout
        cart_products.delete()
        cart.total_amount = 0
        cart.save()

        messages.success(request, "✅ Checkout completed successfully.")
        return render(request, 'medicine_list.html', {
            'items': items,
            'cart': cart,
            'cart_products': [],
            'checkout_success': True,
            'sale': sale
        })

    # ✅ GET request: just show page
    return render(request, 'medicine_list.html', {
        'items': items,
        'cart': cart,
        'cart_products': cart_products,
        'total_amount': cart.total_amount + 5.99 + 1.00,  # Pass the total to template
    })





@login_required
def place_order_view(request):
    user = request.user 
    name = request.GET['name']
    phone = request.GET['phone']
    address = request.GET['address']
    print(name)
    print(phone)
    print(address)


    # ✅ Role check
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'customer':
        messages.error(request, "Only customers can place an order.")
        return redirect('homeview')

    try:
        cart = Cart.objects.get(user=user)
        cart_items = CartProduct.objects.filter(cart=cart)

        if not cart_items.exists():
            messages.warning(request, "Your cart is empty.")
            return redirect('medicine_list')

        # ✅ Create sale
        sale = Sale.objects.create(
            invoice_no=f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            user=user,
            name =name,
            phone =phone,
            address =address,
            total_amount=cart.total_amount
        )

        for cp in cart_items:
            SaleItem.objects.create(
                sale=sale,
                item=cp.item,
                quantity=cp.qty,
                price=cp.price
            )
            # ✅ Reduce stock
            cp.item.item_quantity -= cp.qty
            cp.item.save()

            # ✅ Log stock history
            StockHistory.objects.create(
                item=cp.item,
                action='out',
                quantity=cp.qty,
                note=f"Purchased by {user.username}"
            )

        # ✅ Clear cart
        cart_items.delete()
        cart.total_amount = 0
        cart.save()

        messages.success(request, "Order placed successfully!")
        return redirect('medicine_list')  # Redirect to same page with tab switched to success

    except Cart.DoesNotExist:
        messages.error(request, "No active cart found.")
        return redirect('medicine_list')
    
# def kpaydemo_payment():
#     if request.method == "GET":
#         payment_success = True
#         if payment_success:
#             return 
#         else:
#         pass
#         messages()
#         return redirect('medicine_list')
    



@login_required
def customer_profile_view(request):
    user = request.user

    # ✅ Role check
    if not hasattr(user, 'userprofile') or user.userprofile.role != 'customer':
        messages.error(request, "Only customers can access this page.")
        return redirect('homeview')

    # ✅ Get purchase history
    sales = Sale.objects.filter(user=user).order_by('-created_date')

    return render(request, 'customer_profile.html', {
        'sales': sales
    })


# def chatbot_view(request):
    
#     if request.method == 'POST':
#         questions = request.POST.get('message')
#         cb_data = Chatbot.objects.all()
        
        
#         print(questions)
#         print('This is questions.')
#     return render(request,'customer/dashboard.html')

# def get_chatbot_reply(message):
#     # Basic chatbot logic
#     message = message.lower()

#     if "prescription" in message:
#         return "You can check your prescription status by logging into your account."
#     elif "refill" in message:
#         return "Sure, I can help with that. When was your last refill?"
#     elif "medicine" in message:
#         return "Please provide the name of the medicine you'd like information about."
#     elif "hours" in message or "open" in message:
#         return "Our pharmacy is open from 8 AM to 8 PM, Monday to Saturday."
#     else:
#         return "Sorry, I didn't understand that. Could you please rephrase?"




@csrf_exempt
def chatbot_view(request):
    if request.method == 'POST':
        question = request.POST.get('message', '')
        print(f"User asked: {question}")


    client = genai.Client(api_key="AIzaSyAMUk2hNf5V54vuMUWHMl5nOdes6YDlkX0")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents={question} ,
    )

    # print(response.text)


    return JsonResponse({'reply': response.text })
