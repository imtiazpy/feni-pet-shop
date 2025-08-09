from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='home'),
    path('htmx/', views.htmx_view, name='htmx_view'),
    path('htmx/message/', views.htmx_message, name='htmx_message'),
]