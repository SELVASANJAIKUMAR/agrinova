from django.core.management.base import BaseCommand

from marketplace.models import CropCategory
from marketplace.seed_data import CROP_SEED_DATA


class Command(BaseCommand):
    help = 'Seed predefined Tamil Nadu crop categories'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for crop_data in CROP_SEED_DATA:
            _, was_created = CropCategory.objects.update_or_create(
                name=crop_data['name'],
                defaults={
                    'description': crop_data['description'],
                    'default_image_url': crop_data['default_image_url'],
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {created} created, {updated} updated ({len(CROP_SEED_DATA)} total crops).'
        ))
