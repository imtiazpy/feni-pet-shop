from django import template
from datetime import date, timedelta

register = template.Library()

@register.filter
def expiration_class(expiration_date):
    """Return Tailwind class based on expiration date comparison."""
    if not expiration_date:
        return 'text-base-content'
    
    today = date.today()
    future_30_days = today + timedelta(days=30)
    
    if expiration_date < today:
        return 'text-error'
    elif expiration_date <= future_30_days:
        return 'text-warning'
    return 'text-base-content'


@register.filter
def stock_status_class(stock_item):
    """Return Tailwind badge class for stock item status."""
    today = date.today()
    future_30_days = today + timedelta(days=30)
    
    if stock_item.quantity == 0:
        return 'badge-error'
    elif stock_item.quantity <= 10:
        return 'badge-warning'
    elif stock_item.expiration_date and stock_item.expiration_date < today:
        return 'badge-error'
    elif stock_item.expiration_date and stock_item.expiration_date <= future_30_days:
        return 'badge-warning'
    return 'badge-success'

@register.filter
def stock_status_label(stock_item):
    """Return label for stock item status."""
    today = date.today()
    future_30_days = today + timedelta(days=30)
    
    if stock_item.quantity == 0:
        return 'Out of Stock'
    elif stock_item.quantity <= 10:
        return 'Low Stock'
    elif stock_item.expiration_date and stock_item.expiration_date < today:
        return 'Expired'
    elif stock_item.expiration_date and stock_item.expiration_date <= future_30_days:
        return 'Expiring Soon'
    return 'In Stock'