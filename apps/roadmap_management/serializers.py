# apps/roadmap_management/serializers.py
from rest_framework import serializers
from .models import Roadmaps, AIConfiguration
from apps.user_management.serializers import UserSerializer
from asgiref.sync import sync_to_async
from datetime import datetime

class AIConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConfiguration
        fields = [
            'id', 'model', 'temperature', 'max_tokens', 
            'token_count', 'generation_time', 'created_at', 
            'is_successful', 'error_message'
        ]
        read_only_fields = ['id', 'created_at']

    async def create(self, validated_data):
        """Création asynchrone d'une configuration IA"""
        instance = await sync_to_async(super().create)(validated_data)
        return instance

    async def update(self, instance, validated_data):
        """Mise à jour asynchrone d'une configuration IA"""
        instance = await sync_to_async(super().update)(instance, validated_data)
        return instance

class RoadmapSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Roadmaps
        fields = [
            'id', 'user', 'title', 'content', 
            'version', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'version']

    def validate_status(self, value):
        valid_statuses = ['DRAFT', 'GENERATING', 'COMPLETED', 'ERROR']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value

    async def create(self, validated_data):
        """Création asynchrone d'une roadmap"""
        user = self.context['request'].user
        validated_data['user'] = user
        validated_data['version'] = 1
        
        instance = await sync_to_async(super().create)(validated_data)
        return instance

    async def update(self, instance, validated_data):
        """Mise à jour asynchrone d'une roadmap"""
        if 'content' in validated_data and validated_data['content'] != instance.content:
            instance.version = (instance.version or 0) + 1
        
        instance = await sync_to_async(super().update)(instance, validated_data)
        return instance

class RoadmapDetailSerializer(RoadmapSerializer):
    ai_configs = AIConfigurationSerializer(many=True, read_only=True)

    class Meta(RoadmapSerializer.Meta):
        fields = RoadmapSerializer.Meta.fields + ['content', 'ai_configs']

    async def to_representation(self, instance):
        """Représentation asynchrone détaillée d'une roadmap"""
        data = await sync_to_async(super().to_representation)(instance)
        
        # Récupérer les configurations AI de manière asynchrone
        configs = await instance.ai_configs.all().aasync_all()
        data['ai_configs'] = await sync_to_async(AIConfigurationSerializer(configs, many=True).data)()
        
        return data

class RoadmapUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roadmaps
        fields = ['title', 'content', 'status']

    async def update(self, instance, validated_data):
        """Mise à jour asynchrone avec gestion de version"""
        if 'content' in validated_data and validated_data['content'] != instance.content:
            instance.version = (instance.version or 0) + 1
            instance.updated_at = datetime.now()
            
        instance = await sync_to_async(super().update)(instance, validated_data)
        return instance

    async def validate(self, data):
        """Validation asynchrone des données"""
        data = await sync_to_async(super().validate)(data)
        
        if 'status' in data:
            await sync_to_async(self.validate_status)(data['status'])
        
        return data
class AIConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConfiguration
        fields = [
            'id', 'model', 'temperature', 'max_tokens', 
            'token_count', 'generation_time', 'prompt_template', 
            'presence_penalty', 'frequency_penalty', 'top_p', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']