from django.shortcuts import render



def adminview(request):
    return render(request,'admindashboard.html')


from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages






# def customer_register(request):
#     # ✅ Login ဝင်ပြီးသားဆိုရင် Customer profile ရှိလားစစ်မယ်
#     if request.user.is_authenticated:
#         try:
#             request.user.customer  # မရှိရင် DoesNotExist error တက်မယ်
#             messages.warning(request, "Customer profile ရှိပြီးသား ဖြစ်နေပါတယ်။")
#             return redirect('/')  # သင့်ရဲ့ main/home page ကို redirect လုပ်
#         except Customer.DoesNotExist:
#             pass  # Profile မရှိသေးလို့ register form ကိုပြပေးမယ်

#     if request.method == 'POST':
#         data = request.POST
#         username = data.get('customer[username]')
#         password = data.get('customer[password]')
#         confirm = data.get('customer[confirm_password]')
#         email = data.get('customer[email]')
#         first_name = data.get('customer[first_name]')
#         last_name = data.get('customer[last_name]')
#         phone = data.get('customer[phno]')

#         # ✅ Password check
#         if password != confirm:
#             messages.error(request, "Passwords do not match.")
#             return redirect('customer_register')

#         # ✅ Duplicate username check
#         if User.objects.filter(username=username).exists():
#             messages.error(request, "Username already taken.")
#             return redirect('customer_register')

#         # ✅ Create user
#         user = User.objects.create_user(
#             username=username,
#             password=password,
#             email=email,
#             first_name=first_name,
#             last_name=last_name
#         )

#         # ✅ Login after registration
#         login(request, user)

#         # ✅ Create related Customer profile
#         Customer.objects.create(
#             user=user,
#             phone=phone,
#             address=''  # Or get address from form if you have it
#         )

#         messages.success(request, "Account created and logged in successfully.")

#         # ✅ Next redirect logic
#         next_url = request.GET.get('next')
#         if next_url:
#             return redirect(next_url)

#         return redirect('cart_list')  # Default redirect

#     return render(request, 'register.html')
    

 # views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Role-based redirect
            role = user.userprofile.role
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

# @login_required
# def pharmacist_dashboard(request):
#     profile = get_object_or_404(UserProfile, user=request.user)
#     if request.user.userprofile.role != 'pharmacist':
#         return HttpResponseForbidden("Not allowed")
#     return render(request, 'pharmacist/dashboard.html')