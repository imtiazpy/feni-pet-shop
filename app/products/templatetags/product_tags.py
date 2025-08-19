from django import template
from datetime import date, timedelta

register = template.Library()


@register.filter
def product_status_class(product):
    """Return Tailwind badge class for product stock status."""
    return 'badge-success' if product.is_in_stock else 'badge-error'

@register.filter
def product_status_label(product):
    """Return label for product stock status."""
    return 'In Stock' if product.is_in_stock else 'Out of Stock'