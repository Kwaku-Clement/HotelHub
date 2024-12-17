from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authentication/', include('authentication.urls')),
    path('', include('dashboard.urls')),
    path('rooms/', include('rooms.urls')),
    path('guests/', include('guests.urls')),
    path('reservations/', include('reservations.urls')),
    path('inventory/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    path('reports/', include('reports.urls')),
    path('miscellaneous/', include('miscellaneous.urls')),
]
