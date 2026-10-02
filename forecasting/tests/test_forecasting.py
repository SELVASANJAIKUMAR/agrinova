import pytest
from django.utils import timezone

from forecasting.forecast_engine import forecast_prices
from forecasting.models import PriceRecord


@pytest.mark.django_db
class TestForecasting:
    def test_forecast_with_data(self, crop):
        from datetime import timedelta
        base = timezone.now().date()
        for i in range(12):
            PriceRecord.objects.create(
                crop=crop, district='Chennai',
                price=30 + i,
                date=base - timedelta(days=(12 - i) * 30),
                is_synthetic=True,
            )
        result = forecast_prices(crop, 'Chennai')
        assert 'forecast' in result
        assert len(result['forecast']) == 3

    def test_insufficient_data(self, crop):
        result = forecast_prices(crop, 'Chennai')
        assert 'error' in result

    def test_seed_price_data_command(self, crop):
        from django.core.management import call_command
        call_command('seed_products')
        call_command('seed_price_data', districts=2)
        assert PriceRecord.objects.filter(is_synthetic=True).exists()
