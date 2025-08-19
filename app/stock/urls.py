from django.urls import path
from stock import views

app_name = 'stock'


urlpatterns = [
    path('', views.StockItemListView.as_view(), name="stockitem_list"),
    path('partials/', views.StockItemListPartialView.as_view(), name="stockitem_list_partial"),
    path('search/', views.StockItemSearchView.as_view(), name="stockitem_search"),
    path('create/', views.StockItemCreateView.as_view(), name="stockitem_create"),
    path('<int:pk>/', views.StockItemDetailView.as_view(), name="stockitem_detail"),
    path('<int:pk>/update/', views.StockItemUpdateView.as_view(), name="stockitem_update"),
    path('<int:pk>/adjust/', views.StockItemQuantityAdjustView.as_view(), name="stockitem_adjust"),
    path('<int:pk>/delete/', views.StockItemDeleteView.as_view(), name="stockitem_delete"),
    path('locations/', views.StockLocationListView.as_view(), name="stocklocation_list"),
    path('locations/create/', views.StockLocationCreateView.as_view(), name="stocklocation_create"),
    path('locations/<int:pk>/', views.StockLocationDetailView.as_view(), name="stocklocation_detail"),
    path('locations/<int:pk>/update/', views.StockLocationUpdateView.as_view(), name="stocklocation_update"),
    path('locations/<int:pk>/delete/', views.StockLocationDeleteView.as_view(), name="stocklocation_delete"),
]