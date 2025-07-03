"""
URL configuration for ourproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import *
from django.conf import settings
from django.conf.urls.static import static
from ourapp.views import *

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', login_view, name= 'login'),
    path('logout/', logout_view, name= 'logout'),
    path('customer_register/', customer_register, name= 'customer_register'),
    path('register_customer_ajax/', register_customer_ajax, name='register_customer_ajax'),

    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('pharmacist-dashboard/', pharmacist_dashboard, name='pharmacist_dashboard'),
    path('customer-dashboard/', customer_dashboard, name='customer_dashboard'),
    path('inventory_view/', inventory_view, name= 'inventory_view'),
    path('order_view/', order_view, name= 'order_view'),
    path('SaveOrderView/', SaveOrderView.as_view(), name= 'save_order'),
    path('print-preview/', print_preview, name='print_preview'),
    path('search_customer/', search_customer, name='search_customer'),  

    path('report_view/', report_view, name= 'report_view'),
    path('medicine_list/', medicine_list, name= 'medicine_list'),
    path('medicine_diseaseview/', medicine_diseaseview, name= 'medicine_diseaseview'),
    path('purchase_order/', purchase_order, name= 'purchase_order'),


    path('order/add/<int:item_id>/', add_to_cart, name='add_to_cart'),
    path('order/increase/<int:item_id>/', increase_quantity, name='increase_quantity'),
    path('order/decrease/<int:item_id>/', decrease_quantity, name='decrease_quantity'),
    path('order/update/<int:item_id>/', update_quantity, name='update_quantity'),
    path('order/remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('place-order/', place_order_view, name='place_order'),
    path('customer/profile/', customer_profile_view, name='customer_profile'),

]




