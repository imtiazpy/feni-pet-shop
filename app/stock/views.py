from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from core.mixins import RoleRequiredMixin
from stock.models import StockItem, StockItemTracking, StockLocation
from products.models import Product, Supplier

class StockItemListView(LoginRequiredMixin, ListView):
    model = StockItem
    template_name = 'stock/stockitem_list.html'
    context_object_name = 'stock_items'
    paginate_by = 20

    def get_queryset(self):
        """Optimize query and allow filtering by product or location."""
        queryset = super().get_queryset().select_related('product', 'stock_location', 'supplier', 'created_by')
        product_id = self.request.GET.get('product_id')
        location_id = self.request.GET.get('location_id')
        supplier_id = self.request.GET.get('supplier_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if location_id:
            queryset = queryset.filter(stock_location_id=location_id)
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        return queryset

    def get_context_data(self, **kwargs):
        """Add products and locations for filtering."""
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        context['locations'] = StockLocation.objects.all()
        context['suppliers'] = Supplier.objects.all()
        if self.request.headers.get('HX-Request'):
            context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        return context
    

class StockItemDetailView(LoginRequiredMixin, DetailView):
    model = StockItem
    template_name = 'stock/modals/stockitem_detail_modal.html'
    context_object_name = 'stock_item'

    def get_queryset(self):
        """Optimized query for detail view."""
        return super().get_queryset().select_related('product', 'stock_location', 'supplier', 'created_by')


class StockItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, RoleRequiredMixin, CreateView):
    model = StockItem
    template_name = 'stock/modals/stockitem_create_modal.html'
    permission_required = 'stock.add_stockitem'
    success_url = reverse_lazy('stock:stockitem_list')
    fields = ['product', 'quantity', 'stock_location', 'purchase_price', 'sale_price', 'batch_number', 'expiration_date', 'supplier']
    allowed_roles = ['admin', 'inventory_manager']
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        context['locations'] = StockLocation.objects.all()
        context['suppliers'] = Supplier.objects.all()
        return context

    def form_valid(self, form):
        """Use StockItemManager to create stock and log tracking."""
        try:
            stock_item = StockItem.objects.create_stock(
                product=form.cleaned_data['product'],
                quantity=form.cleaned_data['quantity'],
                stock_location=form.cleaned_data['stock_location'],
                purchase_price=form.cleaned_data['purchase_price'],
                sale_price=form.cleaned_data['sale_price'],
                supplier=form.cleaned_data['supplier'],
                created_by=self.request.user,
                batch_number=form.cleaned_data['batch_number'],
                expiration_date=form.cleaned_data['expiration_date'],
                notes=form.cleaned_data.get('notes', f"Stock added for {form.cleaned_data['product'].name}")
            )
            messages.success(self.request, f"Added {stock_item.quantity} units of {stock_item.product.name} (Batch: {stock_item.batch_number})")
            return HttpResponseRedirect(self.success_url)
        except ValidationError as e:
            form.add_error(None, str(e))
            messages.error(self.request, str(e))
            return self.form_invalid(form)

    

class StockItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, RoleRequiredMixin, UpdateView):
    model = StockItem
    fields = ['quantity', 'stock_location', 'expiration_date', 'supplier']
    template_name = 'stock/modals/stockitem_update_modal.html'
    permission_required = 'stock.change_stockitem'
    success_url = reverse_lazy('stock:stockitem_list')
    context_object_name = "stock_item"
    allowed_roles = ['admin', 'inventory_manager']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suppliers'] = Supplier.objects.all()
        context['stock_locations'] = StockLocation.objects.all()
        return context

    def form_valid(self, form):
        """Use StockItemManager to update stock and log tracking."""
        try:
            stock_item = StockItem.objects.update_stock(
                stock_item=self.object,
                quantity=form.cleaned_data['quantity'],
                stock_location=form.cleaned_data['stock_location'],
                supplier=form.cleaned_data['supplier'],
                expiration_date=form.cleaned_data['expiration_date'],
                notes=form.cleaned_data.get('notes', f"Stock updated for {self.object.product.name}"),
            )
            messages.success(self.request, f"Updated {stock_item.product.name} (Batch: {stock_item.batch_number})")
            # return super().form_valid(form)
            return HttpResponseRedirect(self.success_url)
        except ValidationError as e:
            form.add_error(None, str(e))
            messages.error(self.request, str(e))
            return self.form_invalid(form)

class StockItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, RoleRequiredMixin, DeleteView):
    model = StockItem
    template_name = 'stock/modals/stockitem_confirm_delete.html'
    permission_required = 'stock.delete_stockitem'
    success_url = reverse_lazy('stock:stockitem_list')
    context_object_name = "stock_item"
    allowed_roles = ['admin', 'inventory_manager']

    def get_queryset(self):
        """Optimize query for delete view."""
        return super().get_queryset().select_related('product')

    def form_valid(self, form):
        """Log deletion in StockItemTracking."""
        StockItemTracking.objects.create(
            stock_item=self.object,
            quantity=self.object.quantity,
            movement_type=StockItemTracking.MOVEMENT_TYPES.REMOVE,
            notes=f"Stock deleted for {self.object.product.name} (Batch: {self.object.batch_number})",
            created_by=self.request.user
        )
        messages.success(self.request, f"Deleted {self.object.product.name} (Batch: {self.object.batch_number})")
        return super().form_valid(form)




# StockItemTracking Views
# TODO: add templates for these views and add RoleRequiredMixin


class StockItemTrackingListView(LoginRequiredMixin, ListView):
    model = StockItemTracking
    template_name = 'stock/stockitemtracking_list.html'
    context_object_name = 'tracking_entries'
    paginate_by = 20

    def get_queryset(self):
        """Optimize query and allow filtering by product or movement type."""
        queryset = super().get_queryset().select_related('stock_item__product', 'location_from', 'location_to', 'created_by')
        product_id = self.request.GET.get('product_id')
        movement_type = self.request.GET.get('movement_type')
        if product_id:
            queryset = queryset.filter(stock_item__product_id=product_id)
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        return queryset

    def get_context_data(self, **kwargs):
        """Add products and movement types for filtering."""
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all()
        context['movement_types'] = StockItemTracking.MOVEMENT_TYPES.choices
        return context

class StockItemTrackingDetailView(LoginRequiredMixin, DetailView):
    model = StockItemTracking
    template_name = 'stock/stockitemtracking_detail.html'
    context_object_name = 'tracking_entry'

    def get_queryset(self):
        """Optimize query for detail view."""
        return super().get_queryset().select_related('stock_item__product', 'location_from', 'location_to', 'created_by')