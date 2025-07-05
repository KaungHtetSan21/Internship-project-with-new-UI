from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile
from .models import *


# Inline for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    extra = 0

# Custom User Admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active')
    list_select_related = ('userprofile',)

    def get_role(self, instance):
        return instance.userprofile.role
    get_role.short_description = 'Role'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('userprofile')

    # ✅ This avoids showing profile inline on add form (prevents IntegrityError)
    def get_inline_instances(self, request, obj=None):
        if not obj:  # If adding new User (not editing)
            return []
        return super().get_inline_instances(request, obj)

# Unregister original User admin
admin.site.unregister(User)

# Register the new one
admin.site.register(User, CustomUserAdmin)

# Optional: view UserProfile as standalone
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'role')





class category(admin.ModelAdmin):
    list_display = ['id','name', 'description']
    search_fields = ['name']


class item(admin.ModelAdmin):
    list_display = ('item_name', 'is_limited', 'max_quantity', 'item_price', 'item_quantity', 'exp_date')
    list_filter = ('is_limited', 'category', 'exp_date')
    search_fields = ('item_name', 'brand_name', 'barcode')
    list_editable = ('is_limited', 'max_quantity')  # ✅ Editable from list view

    # ✅ Show is_limited and max_quantity in admin form
    fieldsets = (
        (None, {
            'fields': (
                'item_name', 'category',
                'item_photo', 'item_price', 'item_quantity', 'purcharse_price',
                'item_description', 'exp_date', 'brand_name', 'batch_number',
                'barcode', 'stock_minimum'
            )
        }),
        ('Perception / Limited Settings', {
            'fields': ('is_limited', 'max_quantity'),
            'description': 'Limited stock rule - For example, max 5 per cart.'
        }),
    )

class cart(admin.ModelAdmin):
    list_display = ['id','total_amount']

class cartproduct(admin.ModelAdmin):
    list_display = ['id','item','qty','price']

class stockHistory(admin.ModelAdmin):
    list_display = ('item', 'supplier','action', 'quantity', 'date', 'note')
    list_filter = ( 'supplier','action', 'date')
    search_fields = ('item__item_name', 'supplier__name', 'note')

class supplier(admin.ModelAdmin):
    list_display = ['id','supplier_name','phone']

admin.site.register(Category,category)
admin.site.register(Item,item)
admin.site.register(Cart,cart)
admin.site.register(CartProduct,cartproduct)
admin.site.register(Sale)
admin.site.register(SaleItem)

admin.site.register(StockHistory,stockHistory)
admin.site.register(Possalesreport)
admin.site.register(customerpos)
admin.site.register(Disease)
admin.site.register(Supplier,supplier)

