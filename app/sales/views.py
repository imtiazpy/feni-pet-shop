from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, DetailView, View
from django.http import JsonResponse, HttpResponseRedirect
from django.core.exceptions import ValidationError
from stock.models import StockItem, Product
from sales.models import Sale
from core.mixins import RoleRequiredMixin


# Views:
# Discounted Invoice
# Invoice



class SaleListView(LoginRequiredMixin, ListView):
    template_name = 'sales/sale_list.html'
    model = Sale
    context_object_name = 'sales'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.headers.get('HX-Request'):
            context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class SaleSuccessView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = 'sales/sale_success.html'
    allowed_roles = ['admin', 'inventory_manager', 'cashier']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.headers.get('HX-Request'):
           context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        return context


class SaleCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    template_name = 'sales/sale_create_alpine.html'
    model = Sale
    fields = ['total_amount', 'discount_amount']
    success_url = reverse_lazy('sales:sale_success')
    allowed_roles = ['cashier', 'inventory_manager', 'admin']
    permission_required = 'sales.add_sale'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stock_items'] = StockItem.objects.select_related('product').all()
        if self.request.headers.get('HX-Request'):
            context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        return context

    def post(self, request, *args, **kwargs):
        try:
            item_count = int(request.POST.get('item_count', 0))
            items = []
            for i in range(item_count):
                stock_item_id = request.POST.get(f'stock_item_{i}')
                quantity = request.POST.get(f'quantity_{i}')
                sale_price = request.POST.get(f'sale_price_{i}')
                
                if not all([stock_item_id, quantity, sale_price]):
                    raise ValidationError("All item fields are required.")
                
                stock_item = StockItem.objects.get(id=stock_item_id)
                quantity = int(quantity)
                sale_price = float(sale_price)
                
                items.append({
                    'stock_item': stock_item,
                    'product': stock_item.product,
                    'quantity': quantity,
                    'sale_price': sale_price
                })
            
            discount_amount = float(request.POST.get('discount_amount', 0.00))
            notes = request.POST.get('notes', '')
            
            # Create sale
            sale = Sale.objects.create_sale(
                created_by=self.request.user,
                items=items,
                discount_amount=discount_amount,
                notes=notes
            )
            
            messages.success(self.request, f"Sale #{sale.id} created successfully.")
            return HttpResponseRedirect(self.success_url)
        
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.render_to_response(self.get_context_data(form_error=str(e)))
            
        

class SaleDetailView(LoginRequiredMixin, DetailView):
    template_name = 'sales/modals/sale_detail_modal.html'
    model = Sale
    context_object_name = 'sale'

    def get_queryset(self):
        """Optimized query for detail view."""
        return super().get_queryset().prefetch_related('sale_items')
    


class SalePoSCreateView(LoginRequiredMixin, RoleRequiredMixin, View):
    template_name = 'sales/sale_create_pos.html'
    success_url = reverse_lazy('sales:sale_success')
    allowed_roles = ['cashier', 'inventory_manager', 'admin']
    permission_required = 'sales.add_sale'

    def get(self, request, *args, **kwargs):
        # Initialize cart in session if not present
        if 'pos_cart' not in request.session:
            request.session['pos_cart'] = []
        context = {
            'cart': request.session['pos_cart'],
            'products': Product.objects.all(),
            'stock_items': StockItem.objects.select_related('product').all(),
            'template_to_extend': 'partials/base_empty.html' if request.headers.get('HX-Request') else 'new_dash_base.html'
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        
        if action == 'add_item':
            return self.add_item(request)
        elif action == 'update_quantity':
            return self.update_quantity(request)
        elif action == 'remove_item':
            return self.remove_item(request)
        elif action == 'finalize_sale':
            return self.finalize_sale(request)
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

    def add_item(self, request):
        try:
            barcode = request.POST.get('barcode')
            quantity = int(request.POST.get('quantity', 1))
            
            if quantity < 1:
                raise ValidationError("Quantity must be at least 1.")
            
            # Find StockItem by barcode, preferring oldest batch
            stock_item = StockItem.objects.filter(
                product__barcode=barcode, quantity__gte=quantity
            ).order_by('created_at').first()
            
            if not stock_item:
                raise ValidationError(f"No stock available for barcode {barcode}.")
            
            # Initialize cart if needed
            if 'pos_cart' not in request.session:
                request.session['pos_cart'] = []
            
            # Check if item already in cart
            cart = request.session['pos_cart']
            for item in cart:
                if item['stock_item_id'] == stock_item.id:
                    item['quantity'] += quantity
                    if stock_item.quantity < item['quantity']:
                        raise ValidationError(f"Insufficient stock for {stock_item.product.name}. Available: {stock_item.quantity}")
                    break
            else:
                cart.append({
                    'stock_item_id': stock_item.id,
                    'product_name': stock_item.product.name,
                    'barcode': stock_item.product.barcode,
                    'quantity': quantity,
                    'sale_price': float(stock_item.sale_price or stock_item.product.sale_price),
                    'available_quantity': stock_item.quantity
                })
            
            request.session['pos_cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'cart': cart,
                'message': f"Added {quantity} x {stock_item.product.name} to cart."
            })
        
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def update_quantity(self, request):
        try:
            stock_item_id = int(request.POST.get('stock_item_id'))
            new_quantity = int(request.POST.get('quantity'))
            
            if new_quantity < 1:
                raise ValidationError("Quantity must be at least 1.")
            
            stock_item = StockItem.objects.get(id=stock_item_id)
            if stock_item.quantity < new_quantity:
                raise ValidationError(f"Insufficient stock for {stock_item.product.name}. Available: {stock_item.quantity}")
            
            cart = request.session.get('pos_cart', [])
            for item in cart:
                if item['stock_item_id'] == stock_item_id:
                    item['quantity'] = new_quantity
                    break
            else:
                raise ValidationError("Item not found in cart.")
            
            request.session['pos_cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'cart': cart,
                'message': f"Updated quantity for {stock_item.product.name}."
            })
        
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def remove_item(self, request):
        try:
            stock_item_id = int(request.POST.get('stock_item_id'))
            cart = request.session.get('pos_cart', [])
            cart = [item for item in cart if item['stock_item_id'] != stock_item_id]
            
            request.session['pos_cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'cart': cart,
                'message': "Item removed from cart."
            })
        
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    def finalize_sale(self, request):
        try:
            cart = request.session.get('pos_cart', [])
            if not cart:
                raise ValidationError("Cart is empty.")
            
            discount_amount = float(request.POST.get('discount_amount', 0.00))
            notes = request.POST.get('notes', '')
            
            # Prepare items for SaleManager
            items = []
            for cart_item in cart:
                stock_item = StockItem.objects.get(id=cart_item['stock_item_id'])
                items.append({
                    'stock_item': stock_item,
                    'product': stock_item.product,
                    'quantity': cart_item['quantity'],
                    'sale_price': cart_item['sale_price']
                })
            
            # Create sale
            sale = Sale.objects.create_sale(
                created_by=self.request.user,
                items=items,
                discount_amount=discount_amount,
                notes=notes
            )
            
            # Clear cart
            request.session['pos_cart'] = []
            request.session.modified = True
            
            messages.success(self.request, f"Sale #{sale.id} created successfully.")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': f"Sale #{sale.id} created with {len(items)} items.",
                    'redirect_url': str(self.success_url)
                })
            return HttpResponseRedirect(self.success_url)
        
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)







class SaleReceiptView(View):
    pass


class SaleRefundView(CreateView):
    pass