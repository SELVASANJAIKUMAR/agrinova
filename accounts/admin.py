from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'district', 'is_listing_as_seller', 'is_active_account', 'is_staff')
    list_filter = ('district', 'is_listing_as_seller', 'is_active_account', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('AgriNova Profile', {
            'fields': ('phone', 'village', 'district', 'bio', 'profile_photo', 'is_listing_as_seller', 'is_active_account'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('AgriNova Profile', {
            'fields': ('email', 'phone', 'village', 'district'),
        }),
    )
