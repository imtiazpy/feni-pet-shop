from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import timedelta
from core.mixins import RoleRequiredMixin
from stock.models import StockItem, StockItemTracking
from products.models import Product, Supplier
from sales.models import Sale

def role_required(role):
  def decorator(view_func):
    return user_passes_test(lambda u: u.is_authenticated and getattr(u, 'role', None) == role)(view_func)
  return decorator

@role_required('admin')
def admin_dashboard(request):
  return render(request, 'dashboard/admin_dashboard.html')


class AdminDashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'
    allowed_roles = ['admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.headers.get('HX-Request'):
           context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        return context


class DashboardView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    # TODO: refactor it later
    template_name = 'dashboard/dashboard.html'
    allowed_roles = ['inventory_manager', 'admin']
    permission_required = 'dashboard.view_dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Inventory Metrics
        total_products = Product.objects.count()
        low_stock_threshold = 10  # Configurable threshold
        low_stock_items = StockItem.objects.filter(quantity__lte=low_stock_threshold).count()
        out_of_stock_items = StockItem.objects.filter(quantity=0).count()
        total_stock_quantity = StockItem.objects.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Sales Metrics (today and last 7 days)
        today = timezone.now().date()
        last_week = today - timedelta(days=7)
        sales_today = Sale.objects.filter(created_at__date=today).aggregate(
            count=Count('id'),
            total_revenue=Sum('total_amount')
        )
        sales_last_week = Sale.objects.filter(created_at__date__gte=last_week).aggregate(
            count=Count('id'),
            total_revenue=Sum('total_amount')
        )
        
        # Supplier Metrics
        total_suppliers = Supplier.objects.count()
        supplier_stock_items = Supplier.objects.aggregate(total_items=Count('supplied_items'))['total_items']
        supplier_quantity = Supplier.objects.aggregate(total_quantity=Sum('supplied_items__quantity'))['total_quantity'] or 0
        
        # Recent Stock Movements (last 5)
        recent_movements = StockItemTracking.objects.select_related('stock_item__product').order_by('-created_at')[:5]
        
        context.update({
            # Inventory
            'total_products': total_products,
            'low_stock_items': low_stock_items,
            'out_of_stock_items': out_of_stock_items,
            'total_stock_quantity': total_stock_quantity,
            # Sales
            'sales_today_count': sales_today['count'],
            'sales_today_revenue': sales_today['total_revenue'] or 0,
            'sales_last_week_count': sales_last_week['count'],
            'sales_last_week_revenue': sales_last_week['total_revenue'] or 0,
            # Suppliers
            'total_suppliers': total_suppliers,
            'supplier_stock_items': supplier_stock_items,
            'supplier_quantity': supplier_quantity,
            # Stock Movements
            'recent_movements': recent_movements,
            # Action URLs (adjust to your URL names)
            'create_sale_url': 'sales:sale_create',
            'pos_url': 'sales:sale_pos_create',
            'stock_list_url': 'stock:stock_list',
            'supplier_list_url': 'suppliers:supplier_list',
            'sale_list_url': 'sales:sale_list',
        })

        if self.request.headers.get('HX-Request'):
           context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        
        return context



@role_required('cashier')
def cashier_dashboard(request):
  return render(request, 'dashboard/cashier_dashboard.html')

@role_required('inventory_manager')
def inventory_manager_dashboard(request):
  return render(request, 'dashboard/inventory_manager_dashboard.html')

@role_required('veterinarian')
def veterinarian_dashboard(request):
  return render(request, 'dashboard/veterinarian_dashboard.html')


