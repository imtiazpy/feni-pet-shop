# stock/management/commands/create_dummy_stock.py
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from faker import Faker
from products.models import Product
from stock.models import StockItem, StockItemTracking, StockLocation
from products.models import Supplier

fake = Faker()

User = get_user_model()

class Command(BaseCommand):
    help = "Create dummy StockItem and StockItemTracking records for testing."

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Number of dummy StockItems to create')

    def handle(self, *args, **kwargs):
        total = kwargs['total']
        
        # Fetch dependencies
        products = list(Product.objects.all())
        locations = list(StockLocation.objects.all())
        suppliers = list(Supplier.objects.all())
        users = list(User.objects.filter(is_staff=True))  # Use staff users for created_by

        # Check for required dependencies
        if not products:
            self.stdout.write(self.style.ERROR("Please create some products first (e.g., run create_dummy_products)."))
            return
        if not locations:
            self.stdout.write(self.style.ERROR("Please create some stock locations first."))
            return
        if not suppliers:
            self.stdout.write(self.style.ERROR("Please create some suppliers first."))
            return
        if not users:
            self.stdout.write(self.style.ERROR("Please create some staff users first."))
            return

        created_count = 0
        for _ in range(total):
            try:
                # Randomly select dependencies
                product = random.choice(products)
                # location = random.choice(locations)
                location = StockLocation.objects.get(name="Shelf-A")
                supplier = random.choice(suppliers)
                user = random.choice(users)
                
                # Create StockItem using StockItemManager
                stock_item = StockItem.objects.create_stock(
                    product=product,
                    quantity=random.randint(10, 100),  # Random quantity between 10 and 100
                    stock_location=location,
                    purchase_price=round(random.uniform(50, float(product.sale_price) * 0.9), 2),  # Purchase price < sale price
                    sale_price=product.sale_price,  # Inherit from product
                    supplier=supplier,
                    created_by=user,
                    batch_number=f"{product.sku}-{fake.unique.hexify(text='^^^^^^^^')}",  # Unique batch number
                    expiration_date=fake.date_between(start_date="+30d", end_date="+365d") if random.choice([True, False]) else None,
                    notes=f"Dummy stock for {product.name}"
                )
                created_count += 1
            except ValidationError as e:
                self.stdout.write(self.style.WARNING(f"Failed to create stock item: {str(e)}"))
                continue

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully created {created_count} dummy StockItems with tracking entries."))