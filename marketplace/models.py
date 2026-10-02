from django.conf import settings
from django.db import models

from agrinova.constants import TAMIL_NADU_DISTRICTS, UNIT_CHOICES


class CropCategory(models.Model):
    """Predefined crop types for Tamil Nadu agriculture."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    default_image_url = models.URLField(
        blank=True,
        help_text='Placeholder stock image URL for this crop type',
    )

    class Meta:
        verbose_name_plural = 'Crop categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Listing(models.Model):
    """Seller crop listing on the marketplace."""

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
    )
    crop = models.ForeignKey(CropCategory, on_delete=models.PROTECT, related_name='listings')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    district = models.CharField(max_length=50, choices=TAMIL_NADU_DISTRICTS)
    image = models.ImageField(upload_to='listings/', blank=True, null=True)
    image_url = models.URLField(blank=True, help_text='Fallback stock image URL')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.crop.name} — {self.quantity} {self.unit} ({self.seller.username})'

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return self.crop.default_image_url or ''

    @property
    def total_price(self):
        return self.quantity * self.price_per_unit
