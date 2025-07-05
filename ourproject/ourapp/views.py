






from django.contrib.auth.models import User

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from django.contrib.auth import authenticate, login
from .forms import CustomerRegisterForm
from .models import UserProfile
from django.db.models import Sum






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

@login_required
def pharmacist_dashboard(request):
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden("Pharmacists only.")
    return render(request, 'pharmacist/dashboard.html')

@login_required
def customer_dashboard(request):
    if request.user.userprofile.role != 'customer':
        return HttpResponseForbidden("Customers only.")
    return render(request, 'customer/dashboard.html')










from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from .models import Sale, SaleItem, Cart, CartProduct

@login_required
def report_view(request):
    if request.user.userprofile.role != 'pharmacist':
        return HttpResponseForbidden("Pharmacists only.")

    # ✅ Summary Cards
    total_transactions = Sale.objects.count()
    total_revenue = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    items_sold = SaleItem.objects.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
    avg_margin = 32.5  # Static or dynamic if you have margin logic

    # ✅ Top Selling Products
    top_products = (
        CartProduct.objects
        .values('item__item_name', 'item__category__name')
        .annotate(
            total_qty=Sum('qty'),
            total_revenue=Sum('price')
        )
        .order_by('-total_qty')[:5]
    )

    # ✅ Recent Transactions (POS orders)
    recent_transactions = Cart.objects.filter(user=request.user).order_by('-created_date')[:10]

    # ✅ Pass all context to report.html
    return render(request, 'report.html', {
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
        'items_sold': items_sold,
        'avg_margin': avg_margin,
        'top_products': top_products,
        'recent_transactions': recent_transactions,
    })



def medicine_diseaseview(request):
    return render(request,'medicine&disease.html')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.dateparse import parse_date
from .models import Item, Category

@login_required
def inventory_view(request):
    if request.user.userprofile.role != 'pharmacist':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('login')

    items = Item.objects.all().order_by('-id')
    categories = Category.objects.all()

    # Handle Category Create
    if request.method == 'POST' and 'save_category' in request.POST:
        name = request.POST.get('category_name')
        description = request.POST.get('category_description')
        if name:
            Category.objects.create(name=name, description=description or "")
            messages.success(request, "Category added.")
        else:
            messages.error(request, "Category name is required.")
        return redirect('inventory_view')

    # Handle Item Create & Edit
    if request.method == 'POST' and 'save_item' in request.POST:
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
            'exp_date': parse_date(request.POST.get('exp_date')),
            'brand_name': request.POST.get('brand_name') or '',
            'batch_number': request.POST.get('batch_number') or '',
            'barcode': request.POST.get('barcode') or '',
            'stock_minimum': request.POST.get('stock_minimum') or 10,
            'is_limited': 'is_limited' in request.POST,
            'max_quantity': request.POST.get('max_quantity') or 5,
        }

        if is_edit:
            item = get_object_or_404(Item, id=item_id)
            for field, value in data.items():
                setattr(item, field, value)
            if request.FILES.get('item_photo'):
                item.item_photo = request.FILES['item_photo']
            item.save()
            messages.success(request, "Item updated.")
        else:
            item_photo = request.FILES.get('item_photo')
            Item.objects.create(item_photo=item_photo, **data)
            messages.success(request, "Item created.")

        return redirect('inventory_view')

    # Handle Delete
    if request.method == 'POST' and 'delete_item' in request.POST:
        item_id = request.POST.get('delete_item')
        item = get_object_or_404(Item, id=item_id)
        item.delete()
        messages.success(request, "Item deleted.")
        return redirect('inventory_view')

    return render(request, 'inventory.html', {
        'items': items,
        'categories': categories,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ourapp.models import *
from .models import *
from django.utils import timezone

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

    




# views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Supplier
import json

def purchaseorder_view(request):
    suppliers = Supplier.objects.all()
    return render(request, 'purchaseorder.html', {'suppliers': suppliers})
@csrf_exempt
def create_supplier_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            supplier = Supplier.objects.create(
                supplier_name=data.get('supplier_name'),
                company=data.get('company'),
                contact_person=data.get('contact_person'),
                email=data.get('email'),
                phone=data.get('phone'),
                address=data.get('address'),
                # city=data.get('city'),
                # state=data.get('state'),
                # zip_code=data.get('zip_code'),
                # country=data.get('country'),
                # tax_id=data.get('tax_id'),
                # notes=data.get('notes'),
                status=data.get('is_active', True)
            )
            return JsonResponse({
                'message': 'Supplier added successfully!', 
                # 'supplier_id': supplier.id
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def update_supplier_ajax(request):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            supplier_id = data.get('supplier_id')
            if not supplier_id:
                return JsonResponse({'error': 'Supplier ID is required'}, status=400)
                
            supplier = Supplier.objects.get(id=supplier_id)
            
            fields = [
                'supplier_name', 'company', 'contact_person', 'email', 'phone',
                'address', 'city', 'state', 'zip_code', 'country', 'tax_id', 'notes'
            ]
            
            for field in fields:
                if field in data:
                    setattr(supplier, field, data[field])
            
            if 'is_active' in data:
                supplier.is_active = data['is_active']
            
            supplier.save()
            
            return JsonResponse({
                'message': 'Supplier updated successfully!', 
                'supplier_id': supplier.id
            })
        except Supplier.DoesNotExist:
            return JsonResponse({'error': 'Supplier not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)        

@csrf_exempt
def delete_supplier_ajax(request):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            supplier_id = data.get('supplier_id')
            if not supplier_id:
                return JsonResponse({'error': 'Supplier ID is required'}, status=400)
                
            supplier = Supplier.objects.get(id=supplier_id)
            supplier.delete()
            
            return JsonResponse({
                'message': 'Supplier deleted successfully!'
            })
        except Supplier.DoesNotExist:
            return JsonResponse({'error': 'Supplier not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)



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
    cart.update_total_amount()
    cart.refresh_from_db()

    # ✅ If POST, handle checkout (place order logic)
    if request.method == 'POST' and 'place_order' in request.POST:
        if not cart_products.exists():
            messages.warning(request, "Your cart is empty.")
            return redirect('medicine_list')

        sale = Sale.objects.create(
            invoice_no=f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            user=user,
            total_amount=cart.total_amount
        )

        for cp in cart_products:
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
    })



@login_required
def place_order_view(request):
    user = request.user

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


