# Dateipfad: auth_app/api/urls.py
from django.urls import path
from .views import RegistrationAPIView,LoginAPIView

urlpatterns = [
    path('registration/', RegistrationAPIView.as_view(), name='user-registration'),
    path('login/', LoginAPIView.as_view(), name='user-login'),
]
