from django.urls import path
from stock import views

app_name = 'stock'


urlpatterns = [
    path('', views.StockItemListView.as_view(), name="stockitem_list"),
    path('create/', views.StockItemCreateView.as_view(), name="stockitem_create"),
    path('<int:pk>/', views.StockItemDetailView.as_view(), name="stockitem_detail"),
    path('<int:pk>/update/', views.StockItemUpdateView.as_view(), name="stockitem_update"),
    path('<int:pk>/adjust/', views.StockItemUpdateView.as_view(), name="stockitem_adjust"),
    path('<int:pk>/delete/', views.StockItemDeleteView.as_view(), name="stockitem_delete"),
]