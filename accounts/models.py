from django.contrib.auth.models import AbstractUser
from django.db import models

from agrinova.constants import TAMIL_NADU_DISTRICTS


class User(AbstractUser):
    """Custom user — one account can act as both buyer and seller."""

    phone = models.CharField(max_length=15, blank=True)
    village = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=50, choices=TAMIL_NADU_DISTRICTS, blank=True)
    bio = models.TextField(blank=True, help_text='Farmer or buyer bio')
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_listing_as_seller = models.BooleanField(
        default=False,
        help_text='Whether the user is currently active as a seller',
    )
    is_active_account = models.BooleanField(default=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()
            query = User.objects.filter(email__iexact=self.email)
            if self.pk:
                query = query.exclude(pk=self.pk)
            if query.exists():
                from django.core.exceptions import ValidationError
                raise ValidationError({'email': 'An account with this email already exists.'})

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def location_display(self):
        parts = [p for p in [self.village, self.district] if p]
        return ', '.join(parts) if parts else 'Not set'

