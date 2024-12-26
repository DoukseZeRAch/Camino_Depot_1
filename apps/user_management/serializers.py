# apps/user_management/serializers.py
from rest_framework import serializers
from .models import Users

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'email', 'username', 'role', 'created_at']
        
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Users
        fields = ['email', 'username', 'password', 'role']
    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Veuillez fournir un email valide comme example@domaine.com.")
        if "@" not in value or not value.endswith(('.com', '.fr')):
            raise serializers.ValidationError("L'email doit contenir un '@' et se terminer par '.com' ou '.fr'.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins une lettre.")
        return value

    def validate_role(self, value):
        allowed_roles = ['USER', 'MANAGER', 'ADMIN']
        if value not in allowed_roles:
            raise serializers.ValidationError(
                f"Le rôle '{value}' n'est pas valide. Les rôles acceptés sont : {', '.join(allowed_roles)}."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Users.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['email', 'username', 'is_active', 'role']
        read_only_fields = ['email']  # Email ne peut pas être modifié