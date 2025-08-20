from django.urls import path
from . import views

app_name = 'products'


urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('partials/', views.ProductListPartialView.as_view(), name='product_list_partial'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    # path('price/update/<int:pk>/', views.ProductPriceUpdateView.as_view(), name='product_price_update'),
    
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/partial/', views.SupplierListPartialView.as_view(), name='supplier_list_partial'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/update/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
    # path('price-history/', views.price_history_list, name='price_history_list'),
    # path('price-history/<int:pk>/', views.price_history_detail, name='price_history_detail'),
    # path('price-history/<int:pk>/update/', views.price_history_update, name='price_history_update'),
    # path('price-history/<int:pk>/delete/', views.price_history_delete, name='price_history_delete'),
]