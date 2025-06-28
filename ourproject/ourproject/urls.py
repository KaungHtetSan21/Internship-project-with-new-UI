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

    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('pharmacist-dashboard/', pharmacist_dashboard, name='pharmacist_dashboard'),
    path('customer-dashboard/', customer_dashboard, name='customer_dashboard'),
    path('inventory_view/', inventory_view, name= 'inventory_view'),
    path('order_view/', order_view, name= 'order_view'),
    path('report_view/', report_view, name= 'report_view'),
    path('medicine_list/', medicine_list, name= 'medicine_list'),
    path('medicine_diseaseview/', medicine_diseaseview, name= 'medicine_diseaseview'),
    path('purchase_order/', purchase_order, name= 'purchase_order'),


]




