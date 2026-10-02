from django.contrib import admin

from .models import CropCategory, Listing


@admin.register(CropCategory)
class CropCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_image_url')
    search_fields = ('name',)


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('crop', 'seller', 'quantity', 'unit', 'price_per_unit', 'district', 'is_active', 'created_at')
    list_filter = ('crop', 'district', 'is_active', 'unit')
    search_fields = ('crop__name', 'seller__username', 'description')
