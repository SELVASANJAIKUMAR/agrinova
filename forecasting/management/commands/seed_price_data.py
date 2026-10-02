import math
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from agrinova.constants import TAMIL_NADU_DISTRICTS
from forecasting.models import PriceRecord
from marketplace.models import CropCategory

# Base prices per crop (INR per kg or typical unit) — plausible demo values
BASE_PRICES = {
    'Paddy': 28, 'Sugarcane': 3, 'Banana': 35, 'Coconut': 25, 'Groundnut': 65,
    'Cotton': 55, 'Turmeric': 120, 'Tomato': 30, 'Brinjal': 25, 'Mango': 45,
    'Onion': 35, 'Potato': 28, 'Maize': 22, 'Pearl Millet': 30, 'Finger Millet': 40,
    'Red Gram': 90, 'Black Gram': 85, 'Green Gram': 80, 'Sunflower': 45, 'Sesame': 100,
    'Cashew': 350, 'Coffee': 200, 'Tea': 180, 'Rubber': 150, 'Tapioca': 15,
    'Chilli': 80, 'Coriander': 60, 'Cumin': 200, 'Mustard': 55, 'Wheat': 25,
    'Barley': 22, 'Grapes': 70, 'Papaya': 30, 'Guava': 35, 'Jackfruit': 40,
    'Drumstick': 50, 'Okra': 30, 'Cabbage': 20,
}


class Command(BaseCommand):
    help = 'Generate synthetic historical price data for the last 12 months (demo data)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--districts',
            type=int,
            default=5,
            help='Number of districts to seed per crop (default: 5)',
        )

    def handle(self, *args, **options):
        num_districts = options['districts']
        districts = [d[0] for d in TAMIL_NADU_DISTRICTS[:num_districts]]
        crops = CropCategory.objects.all()
        today = timezone.now().date()
        created = 0

        for crop in crops:
            base = BASE_PRICES.get(crop.name, 40)
            for district in districts:
                # District price variation
                district_factor = 0.9 + (hash(district) % 20) / 100
                price = base * district_factor
                random.seed(hash(f'{crop.name}{district}'))

                for month_offset in range(12, 0, -1):
                    record_date = today - timedelta(days=month_offset * 30)
                    # Seasonal sinusoidal variation + random noise
                    seasonal = math.sin(2 * math.pi * record_date.month / 12) * base * 0.1
                    noise = random.uniform(-base * 0.05, base * 0.05)
                    final_price = max(Decimal('1'), Decimal(str(round(price + seasonal + noise, 2))))

                    _, was_created = PriceRecord.objects.update_or_create(
                        crop=crop,
                        district=district,
                        date=record_date,
                        defaults={
                            'price': final_price,
                            'is_synthetic': True,
                        },
                    )
                    if was_created:
                        created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Synthetic price data seeded. {created} new records created. '
            'NOTE: This is simulated demo data, not real market prices.'
        ))
