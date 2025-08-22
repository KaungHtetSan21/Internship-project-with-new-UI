from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ourapp.views import *
from django.conf.urls.i18n import i18n_patterns  # ✅
# -------------------------------------------------------

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # ✅ language switch url
    path('print-preview/', print_preview, name='print_preview'),
]

urlpatterns += i18n_patterns(  # ✅ this enables language-prefixed URLs
    path('', base, name='base'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    path('forgot_password/', forgot_password_request, name='forgot_password'),
    path('customer_register/', customer_register, name='customer_register'),
    path('verify-otp/', verify_registration_otp, name='verify_registration_otp'),
    path('verify_reset_otp/', verify_reset_otp, name='verify_reset_otp'),
    path('set_new_password/', set_new_password, name='set_new_password'),
    path('reset_password/', reset_password_view, name='reset_password'),
    path('register_customer_ajax/', register_customer_ajax, name='register_customer_ajax'),

    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('pharmacist-dashboard/', pharmacist_dashboard_view, name='pharmacist_dashboard'),
    path('get-order-details/<int:order_id>/', get_order_details, name='get_order_details'),
    path('notification/read/<int:noti_id>/', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('orders/confirm/<int:sale_id>/', confirm_order_view, name='confirm_order'),
    path('orders/cancel/<int:order_id>/', cancel_order_view, name='cancel_order'),
    path('customer_dashboard_view/', customer_dashboard_view, name='customer_dashboard'),
    path('inventory_view/', inventory_view, name='inventory_view'),

    path('send-to-promotion/', send_to_promotion, name="send_to_promotion"),
    path('promotion_area/', promotion_area, name="promotion_area"),
    path("cart/add/<int:item_id>/", add_to_cart, name="add_to_cart"),
    path("cart/add-promo/<int:promo_id>/", add_promo_to_cart, name="add_promo_to_cart"),
    path("cart/increase/<int:cp_id>/", increase_cp_qty, name="increase_cp_qty"),
    path("cart/decrease/<int:cp_id>/", decrease_cp_qty, name="decrease_cp_qty"),
    path("cart/update/<int:cp_id>/", update_cp_qty, name="update_cp_qty"),
    path("cart/remove/<int:cp_id>/", remove_cp, name="remove_cp"),
    path("checkout/", place_order_view, name="place_order"),

    path('order_view/', order_view, name='order_view'),
    path('SaveOrderView/', SaveOrderView.as_view(), name='save_order'),

    path('search_customer/', search_customer, name='search_customer'),

    path('report_view/', report_view, name='report_view'),
    path('medicine_list/', medicine_list, name='medicine_list'),
    path('medicine/edit/<int:item_id>/', edit_item_view, name='edit_item'),
    path('purchaseorder/',purchaseorder_view, name='purchaseorder_view'),
    path('supplier/create-or-update/',create_or_update_supplier, name='create_or_update_supplier'),
    path('supplier/delete/<int:pk>/', delete_supplier, name='delete_supplier'),
    path('place-order/', place_order_view, name='place_order'),
    path('customer/profileview/', customer_profile_view, name='customer_profile'),
    path('customer/profile/', customer_profile, name='customer_profilereal'),
    path('customer/edit-profile/', edit_profile, name='edit_profile'),
    path('medicine/delete/<int:item_id>/', delete_item, name='delete_item'),
    path('chatbot_view/', chatbot_view, name='chatbot_view'),
)

# static files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)