
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
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

class EmailCheckView(APIView):
    """Check if a specific email address is already assigned to a user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Validate query parameter and check user existence."""
        email = request.query_params.get("email")
        if not email:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_email(email)
        except ValidationError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
            
        return self._get_user_response(email)

    def _get_user_response(self, email):
        """Helper to check user existence and respect the 14-line limit."""
        try:
            user = User.objects.get(email=email)
            return Response({
                "id": user.id,
                "email": user.email,
                "fullname": f"{user.first_name} {user.last_name}".strip() or user.username
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
