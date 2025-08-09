from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

handler403 = 'core.views.custom_permission_denied_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('products/', include('products.urls')),
    path('stocks/', include('stock.urls')),
    path('sales/', include('sales.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
