from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

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