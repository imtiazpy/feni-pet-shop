from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext as _
from django_extensions.db.fields import AutoSlugField
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from io import BytesIO
from barcode import Code128
from barcode.writer import ImageWriter
import uuid

from core.models import AbstractBaseModel, AbstractNameDescriptionModel, AbstractStatusModel, AbstractAddressModel


User = get_user_model()


class Supplier(AbstractNameDescriptionModel):
    """
    Model to represent suppliers of products.
    """
    slug = AutoSlugField(_("Slug"), populate_from='name', unique=True, max_length=255)
    email = models.EmailField(_("Contact Email"), blank=True, null=True) 
    phone = models.CharField(_("Contact Phone"), max_length=20, blank=True, null=True)

    @property
    def total_product_items(self):
        """
        Get the total number of products supplied by this supplier.
        """
        return self.supplied_items.count()
    
    def get_product_quantities(self):
        """
        Get the total quantity of products supplied by this supplier.
        """
        result = self.supplied_items.aggregate(total_quantity=Sum('quantity'))
        return result['total_quantity'] or 0
    
    def get_supplied_products(self):
        """
        Get distinct products supplied by this supplier with their total quantities.
        Returns a queryset with product details and aggregated quantities.
        """
        return self.supplied_items.values(
            'product__name',
            'product__barcode',
            'product__image',
            'product__sale_price',
            'product__cost_price'
        ).annotate(total_quantity=Sum('quantity')).order_by('product__name')

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Category(AbstractNameDescriptionModel):
    """
    Model to represent product categories.
    Note: use MPTTModel if we consider deep category hierarchies
    """
    slug = AutoSlugField(_("Slug"), populate_from='name', unique=True, max_length=255)
    parent_category = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL,
        related_name='subcategories',
        blank=True,
        null=True, 
        verbose_name=_("Parent Category")
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['-created_at']
    
    def has_subcategories(self):
        """
        Check if the category has subcategories.
        """
        return self.subcategories.exists()

    def get_all_descendants(self):
        """Get all descendant categories recursively."""
        descendants = []
        for child in self.subcategories.all():
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_all_descendants_ids(self):
        """Get all descendant category IDs efficiently."""
        descendant_ids = []
        for child in self.subcategories.only('pk'):
            descendant_ids.append(child.pk)
            descendant_ids.extend(child.get_all_descendants_ids())
        return descendant_ids

    def get_root_category(self):
        """Get the root (top-level) category for this category."""
        if self.parent_category is None:
            return self
        return self.parent_category.get_root_category()

    def get_level(self):
        """Get the depth level of this category (0 for root categories)."""
        if self.parent_category is None:
            return 0
        return self.parent_category.get_level() + 1

    def __str__(self):
        return self.name


class Product(AbstractNameDescriptionModel):
    """
    Model to represent products in the system.
    """
    slug = AutoSlugField(_("Slug"), populate_from='name', unique=True, max_length=255)
    sku = models.CharField(_("SKU"), max_length=100, unique=True, blank=True, null=True)
    barcode = models.CharField(_("Barcode"), max_length=100, unique=True, blank=True, null=True)
    barcode_image = models.ImageField(_("Barcode Image"), upload_to='barcodes/', blank=True, null=True)
    cost_price = models.DecimalField(
        _("Cost Price"), 
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)]
    )
    sale_price = models.DecimalField(
        _("Price"), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True, related_name='products')
    image = models.ImageField(_("Image"), upload_to='products/', blank=True, null=True)

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    @property
    def is_in_stock(self):
        """
        Check if the product is in stock.
        Returns True if total stock quantity across all StockItems is greater than 0.
        """
        return self.get_total_stock() > 0

    def get_total_stock(self):
        """
        Return the total quantity of this product across all StockItem instances.
        """
        result = self.stock_items.aggregate(total=Sum('quantity'))
        return result['total'] or 0


    def generate_sku(self):
        """Generate sku code for the product"""
        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

    def generate_barcode_image(self):
        """
        Generate a barcode image from the barcode string.
        """
        if not self.barcode:
            self.barcode = f"BAR-{uuid.uuid4().hex[:10].upper()}"

        try:
            barcode_obj = Code128(self.barcode, writer=ImageWriter())
            buffer = BytesIO()
            barcode_obj.write(buffer)
            filename = f"{self.slug.lower().replace(' ', '-')}-barcode.png"
            self.barcode_image.save(filename, File(buffer), save=False)
        except Exception as e:
            raise ValidationError(f"Failed to generate barcode: {str(e)}")

    def save(self, *args, **kwargs):
        """
        Override save to generate barcode and barcode_image on creation and track price history on price updates.
        """
        is_new = self._state.adding
        track_price_history = kwargs.pop('track_price_history', False)
        updated_by = kwargs.pop('updated_by', None)

        # For updates with price history tracking
        # TODO: We will move this logic to signal
        if not is_new and track_price_history and self.pk:
            original = Product.objects.get(pk=self.pk)
            if (original.cost_price != self.cost_price or 
                original.sale_price != self.sale_price):
                PriceHistory.objects.create(
                    product=self,
                    cost_price_old=original.cost_price,
                    cost_price_new=self.cost_price,
                    sale_price_old=original.sale_price,
                    sale_price_new=self.sale_price,
                    created_by=updated_by
                )

        # For new instances, generate barcode and save again
        if is_new:
            self.generate_sku()
            self.generate_barcode_image()
        
        super().save(*args, **kwargs)


class PriceHistory(AbstractBaseModel):
    """
    Model to track price history of products.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_histories')
    cost_price_old = models.DecimalField(_("Old Price"), max_digits=10, decimal_places=2)
    cost_price_new = models.DecimalField(_("New Cost Price"), max_digits=10, decimal_places=2, blank=True, null=True)
    sale_price_old = models.DecimalField(_("Old Sale Price"), max_digits=10, decimal_places=2)
    sale_price_new = models.DecimalField(_("New Sale Price"), max_digits=10, decimal_places=2, blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='price_histories'
    )

    class Meta:
        verbose_name = _("Price History")
        verbose_name_plural = _("Price Histories")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.sale_price_old} to {self.sale_price_new}"


"""
pet_type -> Cat, Dog, Bird etc
category -> Food & Treats, Toys, Accessories, Grooming, Health & Wellness etc
subcategory-> Dry Food, Wet Food, Treats, Chew Toys, Interactive Toys, Collars & Leashes, balls, canned food, shampoo, vitamins and supplements, clothing, beds, litter, etc.
"""
