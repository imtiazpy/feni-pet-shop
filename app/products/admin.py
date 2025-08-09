from django.contrib import admin
from django.utils.html import format_html

from .models import Supplier, Category, Product, PriceHistory

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'cost_price', 'sale_price', 'created_at', 'image_tag', 'barcode_image_tag')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)

    def barcode_image_tag(self, obj):
        if obj.barcode_image:
            return format_html('<img src="{}" style="width: 50px; height: 50px;"/>', obj.barcode_image.url)
        return "No Barcode Image"
    barcode_image_tag.short_description = 'Barcode Image'

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px;"/>', obj.image.url)
        return "No Image"
    
    image_tag.short_description = 'Image'

admin.site.register(Product, ProductAdmin)

admin.site.register(Supplier)
admin.site.register(Category)
admin.site.register(PriceHistory)


