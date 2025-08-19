import uuid
from django.db import models, transaction
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from core.models import AbstractBaseModel, AbstractNameDescriptionModel
from products.models import Product, Supplier


"""
Batch Number (Model) - 
- Batch number with common metadata (expiration, supplier etc) - A dedicated Batch model
- Batch number as string - just a str field in StockItem
"""

User= get_user_model()

# class Warehouse():
#     pass

# class Batch():
#     pass
    

class StockItemManager(models.Manager):
    """
    Custom manager for StockItem to handle creation, updates, and reductions.
    methods: create_stock(), reduce_stock(), update_stock(), transfer_stock()
    """
    
    @transaction.atomic
    def create_stock(self, product, quantity, stock_location=None, purchase_price=None, 
                    sale_price=None, supplier=None, created_by=None, batch_number=None, 
                    expiration_date=None, notes=""):
        """Create a new StockItem and log the addition in StockItemTracking."""
        if quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        stock_item = self.create(
            product=product,
            quantity=quantity,
            stock_location=stock_location,
            purchase_price=purchase_price,
            sale_price=sale_price or product.sale_price,
            supplier=supplier,
            created_by=created_by,
            batch_number=batch_number,
            expiration_date=expiration_date
        )
        StockItemTracking.objects.create(
            stock_item=stock_item,
            quantity=quantity,
            movement_type=StockItemTracking.MOVEMENT_TYPES.ADD,
            notes=notes or f"Initial stock for {product.name}",
            created_by=created_by
        )
        return stock_item

    @transaction.atomic
    def adjust_stock(self, stock_item, quantity, notes="", created_by=None):
        """Adjust StockItem quantity and log changes in StockItemTracking."""
        if not isinstance(quantity, int) or quantity < 0:
            raise ValidationError("Quantity must be a non-negative integer.")
        
        # Fetch the original StockItem for comparison
        old_item = StockItem.objects.get(pk=stock_item.pk)
        old_quantity = old_item.quantity
        
        if quantity == old_quantity:
            return stock_item  # No change, no tracking needed
        
        # Update quantity
        stock_item.quantity = quantity
        stock_item.save()
        
        # Determine movement type and quantity change
        movement_type = 'stock_increase' if quantity > old_quantity else 'stock_decrease'
        quantity_change = abs(quantity - old_quantity)
        
        # Create tracking entry
        notes_content = notes or f"Adjusted quantity for {stock_item.product.name} (Batch: {stock_item.batch_number})"
        notes_content += f"\n Quantity changed from {old_quantity} to {quantity}"
        
        StockItemTracking.objects.create(
            stock_item=stock_item,
            quantity=quantity_change,
            movement_type=movement_type,
            notes=notes_content,
            created_by=created_by
        )
        
        return stock_item

    @transaction.atomic
    def update_stock(self, stock_item, stock_location=None, supplier=None, 
                    purchase_price=None, sale_price=None, expiration_date=None, 
                    notes="", created_by=None):
        """Update StockItem attributes and log changes in StockItemTracking with a list of updated fields."""
        old_item = StockItem.objects.get(pk=stock_item.pk)

        changes = []

        if stock_location is not None and stock_location != old_item.stock_location:
            changes.append(f"stock_location to {stock_location}")
            stock_item.stock_location = stock_location
        
        if supplier is not None and supplier != old_item.supplier:
            changes.append(f"supplier to {supplier or 'None'}")
            stock_item.supplier = supplier
        
        if purchase_price is not None and purchase_price != old_item.purchase_price:
            changes.append(f"purchase_price to {purchase_price or 'None'}")
            stock_item.purchase_price = purchase_price
        
        if sale_price is not None and sale_price != old_item.sale_price:
            changes.append(f"sale_price to {sale_price or 'None'}")
            stock_item.sale_price = sale_price
        
        if expiration_date is not None and expiration_date != old_item.expiration_date:
            changes.append(f"expiration_date to {expiration_date or 'None'}")
            stock_item.expiration_date = expiration_date

        # Save and log only if changes occurred
        if changes:
            stock_item.save()
            # Create notes with list of changed fields
            notes_content = notes or f"Updated {stock_item.product.name} (Batch: {stock_item.batch_number})"
            notes_content += f"\n Changed: {', '.join(changes)}"
            StockItemTracking.objects.create(
                stock_item=stock_item,
                quantity=old_item.quantity,
                movement_type='update',
                notes=notes_content,
                created_by=created_by
            )
        
        return stock_item
 
        

    @transaction.atomic
    def transfer_stock(self, stock_item, quantity, location_to, notes="", created_by=None):
        """Transfer stock to a new location and log in StockItemTracking."""
        if quantity < 0:
            raise ValidationError("Transfer quantity cannot be negative.")
        if quantity > stock_item.quantity:
            raise ValidationError(f"Cannot transfer {quantity} units; only {stock_item.quantity} available.")
        
        # Reduce quantity in original StockItem
        stock_item.quantity -= quantity
        stock_item.save()
        
        # Create or update StockItem at new location
        new_stock_item, created = self.get_or_create(
            product=stock_item.product,
            stock_location=location_to,
            defaults={
                'quantity': quantity,
                'batch_number': stock_item.batch_number,
                'purchase_price': stock_item.purchase_price,
                'sale_price': stock_item.sale_price,
                'supplier': stock_item.supplier,
                'created_by': created_by,
                'expiration_date': stock_item.expiration_date
            }
        )
        if not created:
            new_stock_item.quantity += quantity
            new_stock_item.save()

        # Log transfer
        StockItemTracking.objects.create(
            stock_item=stock_item,
            quantity=quantity,
            movement_type=StockItemTracking.MOVEMENT_TYPES.TRANSFER,
            location_from=stock_item.stock_location,
            location_to=location_to,
            notes=notes or f"Transferred to {location_to.name}",
            created_by=created_by
        )
        return new_stock_item


class StockLocation(AbstractNameDescriptionModel):
    """Location of the stock item in the store. e.g., Shelf A, Shelf B etc"""

    def get_stock_items(self):
        return self.stock_items.count()
    
    def get_stock_quantities(self):
        """
        Get the total quantity of stocks available at this location.
        """
        result = self.stock_items.aggregate(total_quantity=Sum('quantity'))
        return result['total_quantity'] or 0

    def __str__(self):
        return f"{self.name}"


class StockItem(AbstractBaseModel):
    """
    A StockItem represents a quantity of physical instances of a Product.
    Note: now we are using string representation of batch_number. In the future if we decide to manage batch that shares common metadata(e.g. expiration, same supplier etc) across multiple products we will implement Batch Model.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_items")
    quantity = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    expiration_date = models.DateField(blank=True, null=True)
    batch_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    purchase_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)]
    )
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)]
    )
    stock_location = models.ForeignKey(
        StockLocation, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name="stock_items"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, blank=True, null=True, related_name="supplied_items"
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    objects = StockItemManager()

    def generate_batch_number(self):
        if not self.batch_number:
            self.batch_number = f"{self.product.sku}-{uuid.uuid4().hex[:8]}"


    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            self.generate_batch_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name}-Batch: {self.batch_number}"
    
    class Meta:
        verbose_name = "Stock Item"
        verbose_name_plural = "Stock Items"
        ordering = ['-created_at']
        


class StockItemTracking(AbstractBaseModel):
    """who, when, what, and why stock changed"""

    class MOVEMENT_TYPES(models.TextChoices):
        ADD = 'stock_added', 'Stock Added'
        REMOVE = 'stock_removed', 'Stock Removed'
        UPDATE = 'update', 'Update'
        TRANSFER = 'transfer', 'Transfer'
        SALE = 'sale', 'Sale'
        STOCK_INCREASE = 'stock_increase', 'Stock Increase'
        STOCK_DECREASE = 'stock_decrease', 'Stock Decrease'

    stock_item = models.ForeignKey(
        StockItem, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name="tracking"
    )
    quantity = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES.choices)
    notes = models.CharField(
        max_length=100, blank=True, null=True, 
        help_text="String representation of stock item, for reference if stock_item is deleted."
    )
    location_from = models.ForeignKey(
        StockLocation, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="transfer_from",
        help_text="specific to movement_type=transfer"
    )
    location_to = models.ForeignKey(
        StockLocation, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="transfer_to",
        help_text="specific to movement_type=transfer"
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.movement_type}: {self.stock_item or self.notes}"
    
    class Meta:
        verbose_name = "Stock Item Tracking"
        verbose_name_plural = "Stock Items Tracking"
        ordering = ["-created_at"]