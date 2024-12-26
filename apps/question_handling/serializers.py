# backend/apps/question_handling/serializers.py
from rest_framework import serializers
from .models import Questions
from apps.user_management.serializers import UserSerializer
from django.db.models import Max


class QuestionSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Questions
        fields = '__all__'
    

    def validate_text(self, value):

        if value and len(value) > 255:
            raise serializers.ValidationError("Le texte de la question ne doit pas dépasser 500 caractères.")
        """
        Vérifie si une question avec le même texte existe déjà.
        """
        if Questions.objects.filter(text=value).exists():
            raise serializers.ValidationError("Question déjà enregistrée.")
        return value

    def validate_configuration(self, value):
        """
        Valide le champ `configuration` selon le type de question.
        """
        if not value:
            return value

        question_type = self.initial_data.get('type')
        if question_type == 'MULTIPLE_CHOICE':
            options = value.get('options', [])
            if len(options) > 5:
                raise serializers.ValidationError("Maximum 4 options allowed.")
        elif question_type == 'TABLE':
            columns = value.get('columns', 0)
            if columns > 3:
                raise serializers.ValidationError("Maximum 3 columns allowed.")
        
        return value

    def create(self, validated_data):
        """
        Crée une question en attribuant un numéro d'ordre s'il n'est pas défini.
        """
        # Récupérer le dernier numéro d'ordre existant
        last_order = Questions.objects.aggregate(Max("order_num")).get("order_num__max") or 0

        # Attribuer automatiquement le prochain numéro d'ordre si non défini
        if not validated_data.get('order_num'):
            validated_data['order_num'] = last_order + 1

        # Créer la question avec les données validées
        return super().create(validated_data)
