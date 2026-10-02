import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestMarketplace:
    def test_listing_list(self, client, listing):
        resp = client.get(reverse('marketplace:listing_list'))
        assert resp.status_code == 200
        assert b'Paddy' in resp.content

    def test_listing_detail(self, client, listing):
        resp = client.get(reverse('marketplace:listing_detail', args=[listing.pk]))
        assert resp.status_code == 200

    def test_create_listing_requires_login(self, client):
        resp = client.get(reverse('marketplace:listing_create'))
        assert resp.status_code == 302

    def test_seed_products_command(self, db):
        from django.core.management import call_command
        call_command('seed_products')
        assert CropCategory.objects.count() >= 30

from marketplace.models import CropCategory
