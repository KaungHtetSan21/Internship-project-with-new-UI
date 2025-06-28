






from django.contrib.auth.models import User

from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import CustomerRegisterForm
from .models import UserProfile







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
    

 # views.py


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





def report_view(request):
    return render(request,'report.html')

def medicine_list(request):
    return render(request,'medicine_list.html')

def medicine_diseaseview(request):
    return render(request,'medicine&disease.html')

def purchase_order(request):
    return render(request,'purchaseorder.html')
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


def order_view(request):
    if request.user.userprofile.role != 'pharmacist':
        messages.error(request, "You do not have permission to access this page.")
        return redirect('login')

    items = Item.objects.all().order_by('-id')
    categories = Category.objects.all()
    data = {
            # 'category': category,
            'item_name': request.POST.get('item_name'),
            'item_quantity': request.POST.get('item_quantity') or 0,
            'item_price': request.POST.get('item_price') or 0,
            'purcharse_price': request.POST.get('purcharse_price') or 0,
            'item_description': request.POST.get('item_description') or '',
            # 'exp_date': parse_date(request.POST.get('exp_date')),
            'brand_name': request.POST.get('brand_name') or '',
            'batch_number': request.POST.get('batch_number') or '',
            'barcode': request.POST.get('barcode') or '',
            'stock_minimum': request.POST.get('stock_minimum') or 10,
            'is_limited': 'is_limited' in request.POST,
            'max_quantity': request.POST.get('max_quantity') or 5,
        }

    return render(request,'POS.html',{
        'items': items,
        'categories': categories,
    })

