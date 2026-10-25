
from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and check password match."""

    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "repeated_password"]

    def validate(self, data):
        """Ensure that the password and its confirmation match."""
        password = data.get("password")
        repeated_password = data.get("repeated_password")

        if password != repeated_password:
            raise serializers.ValidationError("passwords dont match")
        return data

    def create(self, validated_data):
        """Create a new user with a hashed password."""
        email = validated_data.get("email")
        
        user = User.objects.create_user(
            username=email,  
            email=email,
            password=validated_data.get("password")
        )
        return user

class LoginSerializer(serializers.Serializer):
    """Validate login credentials using email and password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Authenticate user based on provided email and password."""
        email = data.get("email")
        password = data.get("password")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")

        data["user"] = user
        return data
