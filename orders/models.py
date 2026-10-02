from decimal import Decimal

from django.conf import settings
from django.db import models

from agrinova.constants import ORDER_STATUS_CHOICES, PAYMENT_STATUS_CHOICES


class Order(models.Model):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk} — {self.buyer.username}'

    def calculate_total(self):
        total = sum(item.line_total for item in self.items.all())
        self.total_amount = total
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey('marketplace.Listing', on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('order', 'listing')

    def __str__(self):
        return f'{self.listing.crop.name} x {self.quantity}'

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    @property
    def seller(self):
        return self.listing.seller
