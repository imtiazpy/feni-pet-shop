from django.core.management.base import BaseCommand
from faker import Faker
from products.models import Supplier

fake = Faker()

class Command(BaseCommand):
    help = "Create dummy suppliers"

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Number of suppliers to create')

    def handle(self, *args, **kwargs):
        total = kwargs['total']
        for _ in range(total):
            Supplier.objects.create(
                name=fake.company(),
                phone=fake.phone_number(),
                email=fake.email(),
            )
        self.stdout.write(self.style.SUCCESS(f"✅ Created {total} dummy suppliers."))
