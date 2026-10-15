# Dateipfad: auth_app/api/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User

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
        # Username wird auf die E-Mail gesetzt, da Django einen Usernamen zwingend erfordert
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # Fullname sauber splitten und in first_name / last_name eintragen
        name_parts = validated_data['fullname'].split(' ', 1)
        user.first_name = name_parts[0]
        if len(name_parts) > 1:
            user.last_name = name_parts[1]
        user.save()
        
        return user
