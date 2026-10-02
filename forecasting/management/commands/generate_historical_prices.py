from datetime import date
import random

from django.core.management.base import BaseCommand

from forecasting.models import PriceRecord


class Command(BaseCommand):
    help = "Generate synthetic historical monthly price data for 2024 and 2025."

    def handle(self, *args, **options):

        combinations = (
            PriceRecord.objects
            .values_list("crop_id", "district")
            .distinct()
        )

        if not combinations:
            self.stdout.write(
                self.style.ERROR(
                    "No existing crop/district combinations found."
                )
            )
            return

        created = 0
        skipped = 0

        for crop_id, district in combinations:

            existing_prices = list(
                PriceRecord.objects.filter(
                    crop_id=crop_id,
                    district=district
                ).values_list("price", flat=True)
            )

            if not existing_prices:
                continue

            base_price = sum(
                float(price) for price in existing_prices
            ) / len(existing_prices)

            # Generate 2024 full year
            # Generate January-August 2025
            for year in [2024, 2025]:

                last_month = 12 if year == 2024 else 8

                for month in range(1, last_month + 1):

                    record_date = date(year, month, 15)

                    already_exists = PriceRecord.objects.filter(
                        crop_id=crop_id,
                        district=district,
                        date=record_date
                    ).exists()

                    if already_exists:
                        skipped += 1
                        continue

                    seasonal_factor = 1 + (
                        0.10 * random.uniform(-1, 1)
                    )

                    historical_factor = 1 + (
                        0.08 * random.uniform(-1, 1)
                    )

                    price = round(
                        base_price
                        * seasonal_factor
                        * historical_factor,
                        2
                    )

                    PriceRecord.objects.create(
                        crop_id=crop_id,
                        district=district,
                        price=price,
                        date=record_date,
                        is_synthetic=True,
                    )

                    created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Historical data generation completed. "
                f"Created: {created}, Skipped: {skipped}"
            )
        )