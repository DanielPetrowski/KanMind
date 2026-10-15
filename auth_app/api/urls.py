# Dateipfad: auth_app/api/urls.py
from django.urls import path
from .views import RegistrationAPIView

urlpatterns = [
    path('registration/', RegistrationAPIView.as_view(), name='user-registration'),
]
