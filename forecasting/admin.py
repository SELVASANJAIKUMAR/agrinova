from django.contrib import admin

from .models import PriceRecord


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ('crop', 'district', 'price', 'date', 'is_synthetic')
    list_filter = ('crop', 'district', 'is_synthetic', 'date')
