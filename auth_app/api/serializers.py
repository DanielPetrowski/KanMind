
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
