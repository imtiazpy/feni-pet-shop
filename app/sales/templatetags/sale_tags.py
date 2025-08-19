from django import template

register = template.Library()

@register.filter
def sale_status_class(sale):
    """Return Tailwind badge class for sale status."""
    status_map = {
        'completed': 'badge-success',
        'partially_returned': 'badge-warning',
        'fully_returned': 'badge-info',
    }
    return status_map.get(sale.status, 'badge-secondary')

@register.filter
def sale_status_label(sale):
    """Return label for sale status."""
    status_map = {
        'completed': 'Completed',
        'partially_returned': 'Partially Returned',
        'fully_returned': 'Fully Returned',
    }
    return status_map.get(sale.status, 'Unknown')