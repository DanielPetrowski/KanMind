# Dateipfad: core/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Bindet /api/registration/ sauber über das Projekt ein
    path('api/', include('auth_app.api.urls')),
]
