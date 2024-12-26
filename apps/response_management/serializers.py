# apps/response_management/serializers.py
import uuid
from rest_framework import serializers
from .models import Responses, ResponsesBackup
from apps.user_management.models import Users
from apps.question_handling.models import Questions
from asgiref.sync import sync_to_async
from datetime import datetime



class ResponsesSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all(), required=False)
    question = serializers.PrimaryKeyRelatedField(queryset=Questions.objects.all(), required=False)
    
    class Meta:
        model = Responses
        fields = ['id', 'user', 'question', 'content', 'is_complete', 'created_at', 'updated_at', 'draft_data']
    
    def create(self, validated_data):
        """
        Méthode pour créer une réponse et ses backups si nécessaire
        """
        # Créer la réponse principale
        response = Responses.objects.create(**validated_data)
        return response
    
    async def update(self, instance, validated_data):
        """
        Méthode pour mettre à jour une réponse et créer un backup, tout en gérant l'asynchronicité
        """
        # Sauvegarder une ancienne version dans les backups
        if instance.pk:
            backup_count = await sync_to_async(instance.backups.count)()  # Compte des versions existantes
            await sync_to_async(ResponsesBackup.objects.create)(
                response=instance,
                user=instance.user,
                question=instance.question,
                content=instance.content,
                is_complete=instance.is_complete,
                connection_token=self.context.get('token', None),  # Ajouter le token
                version_index=backup_count + 1  # Index incrémenté
            )

        # Mettre à jour les champs de la réponse
        instance.content = validated_data.get('content', instance.content)
        instance.is_complete = validated_data.get('is_complete', instance.is_complete)
        instance.updated_at = validated_data.get('updated_at', datetime.now())
        instance.draft_data = validated_data.get('draft_data', instance.draft_data)
        instance.connection_token = self.context.get('token', instance.connection_token)

        # Sauvegarder les modifications
        await sync_to_async(instance.save)()
        return instance
    def validate_user(self, value):
         
        try:
            return uuid.UUID(str(value))
        except ValueError:
            raise serializers.ValidationError("Le format de l'UUID pour l'utilisateur est invalide.")
  

class ResponsesBackupSerializer(serializers.ModelSerializer):
    response = ResponsesSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all(), required=False)
    question = serializers.PrimaryKeyRelatedField(queryset=Questions.objects.all(), required=False)
    
    class Meta:
        model = ResponsesBackup
        fields = ['id', 'response', 'user', 'question', 'content', 'is_complete', 'backup_at', 'connection_token', 'version_index']
        read_only_fields = ['backup_at', 'version_index']

    def create(self, validated_data):
        """
        Crée un backup pour une réponse
        """
        backup = ResponsesBackup.objects.create(**validated_data)
        return backup
