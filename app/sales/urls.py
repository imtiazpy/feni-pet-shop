from django.urls import path
from sales.views import (
    SaleCreateView, 
    SaleListView, 
    SaleSuccessView, 
    SaleReceiptView, 
    SaleRefundView, 
    SaleDetailView, 
    SalePoSCreateView
)

app_name = 'sales'

urlpatterns = [
    path('', SaleListView.as_view(), name='sale_list'),
    path('success/', SaleSuccessView.as_view(), name="sale_success"),
    path('create/', SaleCreateView.as_view(), name='sale_create'),
    path('pos/', SalePoSCreateView.as_view(), name='sale_pos_create'),
    path('<int:pk>/', SaleDetailView.as_view(), name='sale_detail'),
    path('complete/', SaleCreateView.as_view(), name="sale_complete"),
    path('<int:pk>/receipt/', SaleReceiptView.as_view(), name="sale_receipt"),
    path('<int:pk>/refund/', SaleRefundView.as_view(), name="sale_refund"),
]