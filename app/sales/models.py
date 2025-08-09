from django.db import models, transaction
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from core.models import AbstractBaseModel
from stock.models import StockItem, StockItemTracking
from products.models import Product

User = get_user_model()


"""
Returns, Refunds, Discount
"""

class SaleManager(models.Manager):
    @transaction.atomic
    def create_sale(self, created_by, items, discount_amount=0.00, notes=""):
        """
        Create a sale with multiple items, deduct stock, and log tracking.
        
        Args:
            created_by: User instance who performed the sale.
            items: List of dicts with {stock_item, product, quantity, sale_price}.
            discount_amount: Optional discount amount (default 0.00).
            notes: Optional notes for the sale.
        
        Returns:
            Sale instance.
        
        Raises:
            ValidationError: If stock is insufficient or invalid data provided.
        """
        if not items:
            raise ValidationError("At least one item is required for a sale.")
        
        # Calculate total amount and validate stock
        total_amount = 0
        for item in items:
            stock_item = item['stock_item']
            quantity = item['quantity']
            sale_price = item['sale_price']
            
            if not isinstance(quantity, int) or quantity < 1:
                raise ValidationError(f"Invalid quantity for {stock_item.product.name}: {quantity}")
            if stock_item.quantity < quantity:
                raise ValidationError(f"Insufficient stock for {stock_item.product.name}. Available: {stock_item.quantity}, Requested: {quantity}")
            total_amount += quantity * sale_price
        
        # Apply discount
        if discount_amount < 0:
            raise ValidationError("Discount amount cannot be negative.")
        total_amount -= discount_amount
        if total_amount < 0:
            raise ValidationError("Total amount cannot be negative after discount.")
        
        # Create Sale
        sale = self.create(
            created_by=created_by,
            total_amount=total_amount,
            discount_applied=bool(discount_amount > 0),
            discount_amount=discount_amount,
            status='completed'
        )
        
        # Create SaleItems and update StockItems
        for item in items:
            stock_item = item['stock_item']
            product = item['product']
            quantity = item['quantity']
            sale_price = item['sale_price']
            
            # Create SaleItem
            SaleItem.objects.create(
                sale=sale,
                stock_item=stock_item,
                product=product,
                quantity=quantity,
                sale_price=sale_price
            )
            
            # Deduct stock
            stock_item.quantity -= quantity
            stock_item.save()
            
            # Log in the StockItemTracking
            StockItemTracking.objects.create(
                stock_item=stock_item,
                quantity=quantity,
                movement_type=StockItemTracking.MOVEMENT_TYPES.REMOVE,
                notes=notes or f"Sold {quantity} of {stock_item.product.name} in Sale #{sale.id}",
                created_by=created_by,
                created_at=timezone.now()
            )
        
        return sale

class Sale(AbstractBaseModel):

    class STATUS(models.TextChoices):
        COMPLETED = "completed", "Completed"
        PARTIALLY_RETURNED = "partially_returned", "Partially returned"
        FULLY_RETURNED = "fully_returned", "Fully returned"

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total sale amount after discount."
    )
    discount_applied = models.BooleanField(
        default=False,
        help_text="Indicates if a discount was applied."
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.00)],
        blank=True,
        null=True,
        help_text="Discount amount applied to the sale."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS.choices,
        default='completed',
        help_text="Status of the sale for returns/refunds."
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name="sales", 
        help_text="User who performed the sale (e.g., cashier)."
    )

    objects = SaleManager()

    def __str__(self):
        return f"Sale #{self.id} by {self.created_by} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['created_by']),
        ]
        ordering = ['-created_at']

    @property
    def sub_total(self):
        if self.discount_applied:
            return self.total_amount + self.discount_amount
        return self.total_amount

class SaleItem(AbstractBaseModel):
    """
    Represents an item in a sale, linked to a specific StockItem batch.
    """
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='sale_items',
        help_text="Sale this item belongs to."
    )
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sale_items',
        help_text="StockItem batch sold."
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='sale_items',
        help_text="Product sold (for reference if StockItem is deleted)."
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity sold from this StockItem."
    )
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.00)],
        help_text="Price per unit at the time of sale."
    )

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Sale #{self.sale.id}"

    def clean(self):
        """Validate stock availability before saving."""
        if self.stock_item and self.quantity > self.stock_item.quantity:
            raise ValidationError(f"Insufficient stock for {self.product.name}. Available: {self.stock_item.quantity}, Requested: {self.quantity}")

    class Meta:
        indexes = [
            models.Index(fields=['sale']),
            models.Index(fields=['stock_item']),
        ]

    @property
    def line_total(self):
        return self.quantity * self.sale_price