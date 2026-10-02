import pytest

from accounts.models import User
from marketplace.models import CropCategory, Listing


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        district='Chennai',
    )


@pytest.fixture
def seller(db):
    return User.objects.create_user(
        username='seller1',
        email='seller@example.com',
        password='testpass123',
        district='Coimbatore',
        is_listing_as_seller=True,
    )


@pytest.fixture
def crop(db):
    return CropCategory.objects.create(
        name='Paddy',
        description='Rice crop',
        default_image_url='https://example.com/paddy.jpg',
    )


@pytest.fixture
def listing(db, seller, crop):
    return Listing.objects.create(
        seller=seller,
        crop=crop,
        quantity=100,
        unit='kg',
        price_per_unit=30,
        district='Coimbatore',
        image_url='https://example.com/paddy.jpg',
    )
