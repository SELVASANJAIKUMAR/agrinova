import pytest

from matching.models import BuyerPreference
from matching.scoring import score_listing_for_buyer


@pytest.mark.django_db
class TestMatching:
    def test_same_district_higher_score(self, user, seller, crop, listing):
        user.district = 'Coimbatore'
        user.save()
        listing.district = 'Coimbatore'
        listing.save()
        score_same = score_listing_for_buyer(user, listing, crop_id=crop.id)
        listing.district = 'Chennai'
        listing.save()
        score_diff = score_listing_for_buyer(user, listing, crop_id=crop.id)
        assert score_same > score_diff

    def test_crop_match_matters(self, user, listing, crop):
        score_match = score_listing_for_buyer(user, listing, crop_id=crop.id)
        score_no_match = score_listing_for_buyer(user, listing, crop_id=99999)
        assert score_match > score_no_match
