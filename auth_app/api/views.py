
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from auth_app.api.serializers import UserRegistrationSerializer , LoginSerializer


class RegistrationView(APIView):
    """Handle user registration and return authentication token."""

    permission_classes = []  

    def post(self, request):
        """Validate registration data and create user with token."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                "token": token.key,
                "fullname": f"{user.first_name} {user.last_name}".strip() or user.username,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    """Handle user authentication and issue auth tokens."""

    permission_classes = []  

    def post(self, request):
        """Verify login credentials and return user info with token."""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                "token": token.key,
                "fullname": f"{user.first_name} {user.last_name}".strip() or user.username,
                "email": user.email,
                "user_id": user.id
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
