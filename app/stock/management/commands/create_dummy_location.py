import string
from django.core.management.base import BaseCommand
from faker import Faker
from stock.models import StockLocation

fake = Faker()


class Command(BaseCommand):
    help = "Create dummy StockLocation"

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Number of dummy StockLocation to create')

    def handle(self, *args, **kwargs):
        total = kwargs['total']
        alphabet = list(string.ascii_uppercase)

        for i in range(total):
            name = f"Shelf-{alphabet[i % len(alphabet)]}"
            StockLocation.objects.create(name=name)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Successfully created {total} dummy Stock locations")
        )