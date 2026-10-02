from django.conf import settings
from django.db import models

from agrinova.constants import TAMIL_NADU_DISTRICTS


class BuyerPreference(models.Model):
    """Buyer's stated need for matching recommendations."""

    buyer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='match_preferences',
    )
    crop = models.ForeignKey('marketplace.CropCategory', on_delete=models.CASCADE)
    quantity_needed = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    preferred_district = models.CharField(max_length=50, choices=TAMIL_NADU_DISTRICTS, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.buyer.username} wants {self.crop.name}'
