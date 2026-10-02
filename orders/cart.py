from decimal import Decimal

from django.conf import settings


class Cart:
    """Session-backed shopping cart."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, listing, quantity=1):
        listing_id = str(listing.id)
        if listing_id not in self.cart:
            self.cart[listing_id] = {
                'quantity': str(quantity),
                'price': str(listing.price_per_unit),
            }
        else:
            current = Decimal(self.cart[listing_id]['quantity'])
            self.cart[listing_id]['quantity'] = str(current + Decimal(str(quantity)))
        self.save()

    def update(self, listing_id, quantity):
        listing_id = str(listing_id)
        if listing_id in self.cart:
            if quantity <= 0:
                self.remove(listing_id)
            else:
                self.cart[listing_id]['quantity'] = str(quantity)
                self.save()

    def remove(self, listing_id):
        listing_id = str(listing_id)
        if listing_id in self.cart:
            del self.cart[listing_id]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True

    def save(self):
        self.session.modified = True

    def __iter__(self):
        from marketplace.models import Listing
        listing_ids = self.cart.keys()
        listings = Listing.objects.filter(id__in=listing_ids, is_active=True).select_related('crop', 'seller')
        listing_map = {str(l.id): l for l in listings}
        for listing_id, item in self.cart.items():
            listing = listing_map.get(listing_id)
            if listing:
                yield {
                    'listing': listing,
                    'quantity': Decimal(item['quantity']),
                    'price': Decimal(item['price']),
                    'line_total': Decimal(item['quantity']) * Decimal(item['price']),
                }

    def __len__(self):
        return sum(1 for _ in self)

    @property
    def total(self):
        return sum(item['line_total'] for item in self)

    @property
    def item_count(self):
        return sum(int(Decimal(item['quantity'])) for item in self.cart.values())
