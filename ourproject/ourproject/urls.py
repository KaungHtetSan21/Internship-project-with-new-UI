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
    path('send_to_promotion/', send_to_promotion, name='send_to_promotion'),
    path('order_view/', order_view, name= 'order_view'),
    path('SaveOrderView/', SaveOrderView.as_view(), name= 'save_order'),
    path('print-preview/', print_preview, name='print_preview'),
    path('search_customer/', search_customer, name='search_customer'),  

    path('report_view/', report_view, name= 'report_view'),
    path('medicine_list/', medicine_list, name= 'medicine_list'),
  
    path('medicine/edit/<int:item_id>/', edit_item_view, name='edit_item'), 

    path('purchaseorder/', purchaseorder_view, name='purchaseorder_view'),
    path('create_supplier_ajax/', create_supplier_ajax, name='create_supplier_ajax'),
    path('update_supplier_ajax/', update_supplier_ajax, name='update_supplier_ajax'),
    path('delete_supplier_ajax/', delete_supplier_ajax, name='delete_supplier_ajax'),

    path('order/add/<int:item_id>/', add_to_cart, name='add_to_cart'),
    path('order/increase/<int:item_id>/', increase_quantity, name='increase_quantity'),
    path('order/decrease/<int:item_id>/', decrease_quantity, name='decrease_quantity'),
    path('order/update/<int:item_id>/', update_quantity, name='update_quantity'),
    path('order/remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('place-order/', place_order_view, name='place_order'),
    path('customer/profile/', customer_profile_view, name='customer_profile'),
    path('medicine/delete/<int:item_id>/', delete_item, name='delete_item'),

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


