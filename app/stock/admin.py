from django.contrib import admin

from stock.models import StockItem, StockItemTracking, StockLocation

admin.site.register(StockItem)

admin.site.register(StockLocation)

admin.site.register(StockItemTracking)
