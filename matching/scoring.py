"""Explainable buyer-seller matching scoring."""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from agrinova.constants import TAMIL_NADU_REGIONS
from marketplace.models import Listing


def _get_region(district):
    for region, districts in TAMIL_NADU_REGIONS.items():
        if district in districts:
            return region
    return None


def _district_score(buyer_district, seller_district):
    if not buyer_district or not seller_district:
        return 0.3
    if buyer_district == seller_district:
        return 1.0
    buyer_region = _get_region(buyer_district)
    seller_region = _get_region(seller_district)
    if buyer_region and buyer_region == seller_region:
        return 0.6
    return 0.2


def _quantity_score(needed_qty, available_qty):
    if not needed_qty or not available_qty:
        return 0.5
    needed = Decimal(str(needed_qty))
    available = Decimal(str(available_qty))
    if available >= needed:
        return 1.0
    ratio = float(available / needed)
    return max(0.2, min(ratio, 0.9))


def _recency_score(created_at):
    days_old = (timezone.now() - created_at).days
    if days_old <= 7:
        return 1.0
    if days_old <= 30:
        return 0.7
    if days_old <= 90:
        return 0.4
    return 0.2


def score_listing_for_buyer(buyer, listing, crop_id=None, quantity_needed=None, preferred_district=None):
    """
    Score a listing for a buyer need.

    Weights: crop match 40%, district 30%, quantity 20%, recency 10%.
    Returns float 0-100.
    """
    score = 0.0
    weights = {'crop': 40, 'district': 30, 'quantity': 20, 'recency': 10}

    # Crop match
    target_crop = crop_id or (buyer.match_preferences.crop_id if hasattr(buyer, 'match_preferences') and buyer.match_preferences else None)
    if target_crop:
        crop_match = 1.0 if listing.crop_id == int(target_crop) else 0.0
    else:
        crop_match = 0.5
    score += weights['crop'] * crop_match

    # District proximity
    buyer_district = preferred_district or buyer.district
    district_match = _district_score(buyer_district, listing.district)
    score += weights['district'] * district_match

    # Quantity fit
    qty_needed = quantity_needed
    if hasattr(buyer, 'match_preferences') and buyer.match_preferences and not qty_needed:
        qty_needed = buyer.match_preferences.quantity_needed
    qty_match = _quantity_score(qty_needed, listing.quantity)
    score += weights['quantity'] * qty_match

    # Recency
    recency = _recency_score(listing.created_at)
    score += weights['recency'] * recency

    return round(score, 1)


def get_recommended_sellers_for_buyer(buyer, crop_id=None, quantity_needed=None, preferred_district=None, limit=5):
    """Return top matching listings for a buyer."""
    listings = Listing.objects.filter(is_active=True).exclude(seller=buyer).select_related('crop', 'seller')
    if crop_id:
        listings = listings.filter(crop_id=crop_id)

    scored = []
    for listing in listings:
        s = score_listing_for_buyer(buyer, listing, crop_id, quantity_needed, preferred_district)
        scored.append((listing, s))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [{'listing': l, 'score': s} for l, s in scored[:limit] if s >= 30]


def get_recommended_buyers_for_seller(seller, limit=5):
    """Find buyers whose preferences match seller's active listings."""
    from accounts.models import User
    from matching.models import BuyerPreference

    listings = Listing.objects.filter(seller=seller, is_active=True).select_related('crop')
    if not listings.exists():
        return []

    results = []
    preferences = BuyerPreference.objects.select_related('buyer', 'crop').all()
    for pref in preferences:
        if pref.buyer == seller:
            continue
        best_score = 0
        best_listing = None
        for listing in listings:
            s = score_listing_for_buyer(
                pref.buyer, listing,
                crop_id=pref.crop_id,
                quantity_needed=pref.quantity_needed,
                preferred_district=pref.preferred_district,
            )
            if s > best_score:
                best_score = s
                best_listing = listing
        if best_score >= 30:
            results.append({
                'buyer': pref.buyer,
                'score': best_score,
                'listing': best_listing,
                'preference': pref,
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]
