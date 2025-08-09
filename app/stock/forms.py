# from django import forms
# from .models import StockItem, StockItemTracking, StockLocation
# from products.models import Product
# from products.models import Supplier

# class StockItemForm(forms.ModelForm):
#     notes = forms.CharField(max_length=100, required=False, help_text="Additional notes for stock operation.")

#     class Meta:
#         model = StockItem
#         fields = ['product', 'quantity', 'stock_location', 'purchase_price', 'sale_price', 'batch_number', 'expiration_date', 'supplier']

#     def clean(self):
#         cleaned_data = super().clean()
#         quantity = cleaned_data.get('quantity')
#         if quantity is not None and quantity < 0:
#             raise forms.ValidationError("Quantity cannot be negative.")
#         batch_number = cleaned_data.get('batch_number')
#         if batch_number and StockItem.objects.filter(batch_number=batch_number).exclude(pk=self.instance.pk).exists():
#             raise forms.ValidationError("Batch number must be unique.")
#         return cleaned_data

# class StockItemTrackingForm(forms.ModelForm):
#     class Meta:
#         model = StockItemTracking
#         fields = ['stock_item', 'quantity', 'movement_type', 'notes', 'location_from', 'location_to', 'created_by']