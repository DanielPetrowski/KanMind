
from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Validate registration data and check password match."""

    fullname = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "fullname", "email", "password", "repeated_password"]

    def validate_email(self, value):
        """Check if the email address is already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


    def validate(self, data):
        """Ensure that the password and its confirmation match."""
        password = data.get("password")
        repeated_password = data.get("repeated_password")

        if password != repeated_password:
            raise serializers.ValidationError("passwords dont match")
        return data

    def create(self, validated_data):
        """Create user with hashed password and email as username."""
        return User.objects.create_user(
            username=validated_data.get("email"),
            email=validated_data.get("email"),
            password=validated_data.get("password"),
            first_name=validated_data.get("fullname", "")
        )


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

class UserSummarySerializer(serializers.ModelSerializer):
    """A minimal representation of a user for relations."""

    fullname = serializers.CharField(source="first_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "fullname", "email"]
