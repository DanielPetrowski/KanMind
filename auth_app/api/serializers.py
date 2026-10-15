# Dateipfad: auth_app/api/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class RegistrationSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        # Explizite Angabe und Reihenfolge laut Request-Body-Vorgabe
        fields = ["fullname", "email", "password", "repeated_password"]
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'email': {'required': True}
        }

    def validate(self, attrs):
        # Validierung des Zusammenhangs zwischen Passwort und repeated_password
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError({"repeated_password": "Die Passwörter stimmen nicht überein."})
        
        # Prüfen, ob die E-Mail bereits existiert
        if User.objects.filter(username=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Ein Benutzer mit dieser E-Mail existiert bereits."})
            
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # Wir teilen den Namen in eine Liste auf
        name_parts = validated_data['fullname'].split(' ', 1)
        
        # .pop(0) holt sicher das erste Wort heraus (Vorname)
        user.first_name = name_parts.pop(0)
        
        # Wenn noch ein Wort übrig ist, ist das der Nachname
        if name_parts:
            user.last_name = name_parts.pop(0)
            
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError("E-Mail und Passwort sind erforderlich.")

        # Authentifizierung über die E-Mail (da diese als Username dient)
        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Ungültige E-Mail-Adresse oder Passwort.")
            
        if not user.is_active:
            raise serializers.ValidationError("Dieser Benutzeraccount ist deaktiviert.")

        # Wir speichern den validierten User in den Attributen für die View
        attrs["user"] = user
        return attrs