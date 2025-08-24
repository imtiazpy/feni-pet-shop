from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Prefetch, Q
from django.http import JsonResponse

from .models import Product, Category, Supplier
from core.mixins import RoleRequiredMixin


class ProductListPartialView(LoginRequiredMixin, ListView):
    """For Search result"""
    model = Product
    template_name = 'products/partials/product_list_partial.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')
        search = self.request.GET.get('search')

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(barcode__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')
        category_id = self.request.GET.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        if self.request.headers.get('HX-Request'):
            context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        return context

class ProductCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Product
    template_name = 'products/modals/product_create_modal.html'
    fields = ['name', 'description', 'cost_price', 'sale_price', 'category', 'image']
    success_url = reverse_lazy('products:product_list')
    allowed_roles = ['admin', 'inventory_manager']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

    def form_valid(self, form):
        messages.success(self.request, "Product created successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating the product. Please check the form and try again.")
        return super().form_invalid(form)


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'products/modals/product_detail_modal.html'


class ProductUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Product
    template_name = 'products/modals/product_update_modal.html'
    fields = ['name', 'description', 'category', 'image']
    success_url = reverse_lazy('products:product_list')
    allowed_roles = ['admin', 'inventory_manager']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Product updated successfully.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the product. Please check the form and try again.")
        return super().form_invalid(form)

        
class ProductDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/modals/product_confirm_delete.html'
    success_url = reverse_lazy('products:product_list')
    allowed_roles = ['admin', 'inventory_manager']

    def form_valid(self, form):
        messages.success(self.request, "Product deleted successfully.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There was an error deleting the product.")
        return super().form_invalid(form)


class ProductPriceUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    # TODO: We need to add mechanism to update StockItem prices when updating prices for a product

    model = Product
    fields = ['cost_price', 'sale_price']
    template_name = 'products/modals/price_update_modal.html'
    context_object_name = 'product'
    success_url = reverse_lazy('products:product_list')
    allowed_roles = ['admin', 'inventory_manager']

    def form_valid(self, form):
        form.instance.save(track_price_history=True, updated_by=self.request.user)
        messages.success(self.request, "Product price updated successfully.")
        return redirect(self.get_success_url())
        
    def form_invalid(self, form):
        messages.error(self.request, "Failed to update price. Please check the inputs.")
        return super().form_invalid(form)


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.headers.get('HX-Request'):
            context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        return context


class CategoryCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Category
    template_name = 'products/modals/category_create_modal.html'
    fields = ['name', 'description', 'parent_category']
    success_url = reverse_lazy('products:category_list')
    allowed_roles = ['admin', 'inventory_manager']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parent_categories'] = Category.objects.all()
        return context
        
    def form_valid(self, form):
        messages.success(self.request, "Category created successfully.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating the category. Please check the form and try again.")
        return super().form_invalid(form)


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'products/modals/category_detail_modal.html'
    context_object_name = 'category'

    def get_queryset(self):
        return Category.objects.prefetch_related('products')


class CategoryUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Category
    template_name = 'products/modals/category_update_modal.html'
    fields = ['name', 'description', 'parent_category']
    success_url = reverse_lazy('products:category_list')
    allowed_roles = ['admin', 'inventory_manager']
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
         # Get descendant IDs efficiently using the model method
        excluded_ids = [self.object.pk] + self.object.get_all_descendants_ids()
        
        # Only select necessary fields for performance
        context['categories'] = Category.objects.exclude(
            pk__in=excluded_ids
        ).only('pk', 'name', 'parent_category').order_by('name')
        
        return context
        
    def form_valid(self, form):
        messages.success(self.request, "Category updated successfully.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the category. Please check the form and try again.")
        return super().form_invalid(form)
    

class CategoryDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Category
    template_name = 'products/modals/category_confirm_delete.html'
    success_url = reverse_lazy('products:category_list')
    allowed_roles = ['admin', 'inventory_manager']

    def form_valid(self, form):
        messages.success(self.request, "Category deleted successfully.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There was an error deleting the category")
        return super().form_invalid(form)



class SupplierListPartialView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'products/partials/supplier_list_partial.html'
    context_object_name = 'suppliers'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'products/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.headers.get('HX-Request'):
            context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'
        return context


class SupplierCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Supplier
    template_name = 'products/modals/supplier_create_modal.html'
    fields = ['name', 'description', 'email', 'phone']
    success_url = reverse_lazy('products:supplier_list')
    allowed_roles = ['admin', 'inventory_manager']

    def form_valid(self, form):
        messages.success(self.request, "Supplier created successfully.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There was an error creating the Supplier. Please check the form and try again.")
        return super().form_invalid(form)


class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'products/modals/supplier_detail_modal.html'
    context_object_name = 'supplier'
    

class SupplierUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Supplier
    template_name = 'products/modals/supplier_update_modal.html'
    fields = ['name', 'description', 'phone', 'email']
    success_url = reverse_lazy('products:supplier_list')
    allowed_roles = ['admin', 'inventory_manager']

    def form_valid(self, form):
        messages.success(self.request, "Supplier updated successfully.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the supplier. Please check the form and try again.")
        return super().form_invalid(form)
    

class SupplierDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'products/modals/supplier_confirm_delete.html'
    success_url = reverse_lazy('products:supplier_list')
    allowed_roles = ['admin', 'inventory_manager']

    def form_valid(self, form):
        messages.success(self.request, "Supplier deleted successfully.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "There was an error deleting the supplier. Please try again.")
        return super().form_invalid(form)
    



class GenerateLabelView(LoginRequiredMixin, TemplateView):
    template_name = 'products/generate_label.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all().order_by('-created_at')

        if self.request.headers.get('HX-Request'):
            context['template_to_extend'] = 'partials/base_empty.html'
        else:
            context['template_to_extend'] = 'new_dash_base.html'

        return context

    def post(self, request, *args, **kwargs):
        try:
            product_id = request.POST.get('product_id')
            if not product_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please select a product'
                }, status=400)

            product = get_object_or_404(Product, id=product_id)
            
            # Generate barcode if not exists
            barcode = product.barcode or f"PET{str(product.id).zfill(6)}"
            
            return JsonResponse({
                'status': 'success',
                'barcode': barcode,
                'name': product.name,
                'price': float(product.sale_price) if product.sale_price else 0.00,
                'category': product.category.name if hasattr(product, 'category') and product.category else 'N/A'
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Product not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while generating the label'
            }, status=500)

