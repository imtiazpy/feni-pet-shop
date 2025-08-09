# dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('cashier/', views.cashier_dashboard, name='cashier'),
    path('manager/', views.inventory_manager_dashboard, name='inventory_manager'),
    path('veterinarian/', views.veterinarian_dashboard, name='veterinarian'),
]
