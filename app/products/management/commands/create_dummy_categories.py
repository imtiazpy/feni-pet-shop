from django.core.management.base import BaseCommand
from faker import Faker
from products.models import Category

fake = Faker()

class Command(BaseCommand):
    help = "Create dummy product categories"

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Number of categories to create')

    def handle(self, *args, **kwargs):
        total = kwargs['total']
        for _ in range(total):
            name = fake.unique.word().capitalize() + " Products"
            Category.objects.create(name=name)
        self.stdout.write(self.style.SUCCESS(f"✅ Created {total} dummy categories."))
