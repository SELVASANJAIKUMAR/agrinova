from django.contrib import admin

from .models import BuyerPreference


@admin.register(BuyerPreference)
class BuyerPreferenceAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'crop', 'quantity_needed', 'preferred_district', 'updated_at')
