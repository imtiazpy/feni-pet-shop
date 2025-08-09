import random
from django.core.management.base import BaseCommand
from faker import Faker
from products.models import Product, Category, Supplier

fake = Faker()

class Command(BaseCommand):
    help = "Create dummy products for testing"

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Number of dummy products to create')

    def handle(self, *args, **kwargs):
        total = kwargs['total']
        categories = list(Category.objects.all())
        suppliers = list(Supplier.objects.all())

        if not categories or not suppliers:
            self.stdout.write(self.style.ERROR("Please create some categories and suppliers first."))
            return

        for i in range(total):
            name = fake.unique.company() + " " + fake.word()
            product = Product.objects.create(
                name=name,
                cost_price=round(random.uniform(50, 300), 2),
                sell_price=round(random.uniform(301, 600), 2),
                expiation_date=fake.date_between(start_date="+30d", end_date="+365d"),
                category=random.choice(categories),
                supplier=random.choice(suppliers)
            )
            product.save()

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully created {total} dummy products."))
