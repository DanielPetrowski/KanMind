# Dateipfad: auth_app/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from .serializers import RegistrationSerializer

class RegistrationAPIView(APIView):
    # Offener Endpunkt laut Vorgabe ("No Permissions required")
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        
        # Saubere Standard-Validierung ohne Tippfehler
        if serializer.is_valid():
            user = serializer.save()
            
            # Token generieren
            token, created = Token.objects.get_or_create(user=user)
            
            # Fullname wieder zusammensetzen für die Response
            fullname = f"{user.first_name} {user.last_name}".strip() or user.username
            
            # Exakte Success Response Struktur laut deiner Vorgabe
            response_data = {
                "token": token.key,
                "fullname": fullname,
                "email": user.email,
                "user_id": user.id
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
