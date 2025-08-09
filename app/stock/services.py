# from django.db import transaction
# from .models import StockItem, StockItemTracking

# def adjust_stock(stock_item, quantity, movement_type, notes=""):
#     with transaction.atomic():
#         if movement_type == "REMOVE" and stock_item.quantity < quantity:
#             raise ValueError("Insufficient stock")
#         stock_item.quantity += quantity if movement_type == "ADD" else -quantity
#         stock_item.save()
#         StockItemTracking.objects.create(
#             stock_item=stock_item,
#             quantity=abs(quantity),
#             movement_type=movement_type,
#             notes=notes
#         )