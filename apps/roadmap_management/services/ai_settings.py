# apps/roadmap_management/models/ai_settings.py

from __future__ import annotations
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from dataclasses import dataclass
from typing import Dict, Any, Optional
import uuid
import time
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from roadmap_management.models import Roadmaps  # uniquement pour le type checking

logger = logging.getLogger(__name__)

@dataclass
class AIModelConfig:
    """Configuration pour les modèles AI supportés"""
    name: str
    max_tokens: int
    min_temperature: Decimal
    max_temperature: Decimal

class AIConfigurationTemplate(models.Model):
    """Templates de configuration IA réutilisables"""
    
    # Constantes de classe
    SUPPORTED_MODELS = {
        "gpt-4": AIModelConfig("GPT-4", 8192, Decimal("0.0"), Decimal("1.0")),
        "gpt-4-turbo": AIModelConfig("GPT-4 Turbo", 32768, Decimal("0.0"), Decimal("1.0")),
        "gpt-3.5-turbo": AIModelConfig("GPT-3.5 Turbo", 4096, Decimal("0.0"), Decimal("1.0"))
    }
    
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nom unique de la configuration"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description détaillée de l'utilisation prévue"
    )
    model = models.CharField(
        max_length=50,
        choices=[(k, v.name) for k, v in SUPPORTED_MODELS.items()],
        default="gpt-4"
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="Température pour la génération (0.0 - 1.0)"
    )
    max_tokens = models.IntegerField(
        default=4096,
        help_text="Nombre maximum de tokens pour la réponse"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Indique si cette configuration est la configuration par défaut"
    )
    created_by = models.ForeignKey(
        'user_management.Users',
        on_delete=models.PROTECT,
        help_text="Utilisateur ayant créé la configuration"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_configuration_templates'
        ordering = ['-updated_at']

    def clean(self):
        """Valide les contraintes métier du modèle"""
        if not 0 <= self.temperature <= 1:
            raise ValidationError("La température doit être entre 0 et 1")
            
        if not 1000 <= self.max_tokens <= 32000:
            raise ValidationError("max_tokens doit être entre 1000 et 32000")

    def save(self, *args: Any, **kwargs: Any):
        """Sauvegarde avec validation et gestion du template par défaut"""
        self.clean()
        if self.is_default:
            # Désactive les autres templates par défaut
            type(self).objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class GenerationHistory(models.Model):
    """Historique des générations de roadmaps"""
    
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4, editable=False)
    roadmap = models.ForeignKey(
        'Roadmaps',
        on_delete=models.CASCADE,
        related_name='generation_history'
    )
    configuration_used = models.JSONField()
    prompt_used = models.TextField()
    token_count = models.IntegerField()
    generation_time = models.FloatField(help_text="Temps de génération en secondes")
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'generation_history'
        ordering = ['-created_at']

class AISettingsService:
    """Service de gestion des paramètres IA"""

    @staticmethod
    def get_default_configuration() -> Dict[str, Any]:
        """Récupère la configuration par défaut"""
        try:
            config = AIConfigurationTemplate.objects.filter(is_default=True).first()
            if not config:
                config = AIConfigurationTemplate.objects.first()
            
            if config:
                return {
                    'model': config.model,
                    'temperature': float(config.temperature),
                    'max_tokens': config.max_tokens
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la configuration par défaut: {e}")
            
        return {
            'model': getattr(settings, 'DEFAULT_AI_MODEL', 'gpt-4'),
            'temperature': float(getattr(settings, 'DEFAULT_AI_TEMPERATURE', 0.7)),
            'max_tokens': int(getattr(settings, 'DEFAULT_AI_MAX_TOKENS', 4096))
        }

    @staticmethod
    def validate_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
        """Valide une configuration"""
        validated = {}
        
        if 'temperature' in config:
            temp = float(config['temperature'])
            if 0 <= temp <= 1:
                validated['temperature'] = temp
            else:
                raise ValidationError("La température doit être entre 0 et 1")

        if 'model' in config:
            model = config['model']
            if model in AIConfigurationTemplate.SUPPORTED_MODELS:
                validated['model'] = model
            else:
                raise ValidationError(
                    f"Modèle non supporté. Options: "
                    f"{', '.join(AIConfigurationTemplate.SUPPORTED_MODELS.keys())}"
                )

        if 'max_tokens' in config:
            tokens = int(config['max_tokens'])
            if 1000 <= tokens <= 32000:
                validated['max_tokens'] = tokens
            else:
                raise ValidationError("max_tokens doit être entre 1000 et 32000")

        return validated

    @staticmethod
    async def log_generation(
        roadmap: 'Roadmaps',
        configuration: Dict[str, Any],
        prompt: str,
        token_count: int,
        start_time: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Enregistre les détails d'une génération"""
        try:
            generation_time = time.time() - start_time
            
            await GenerationHistory.objects.acreate(
                roadmap=roadmap,
                configuration_used=configuration,
                prompt_used=prompt,
                token_count=token_count,
                generation_time=generation_time,
                success=success,
                error_message=error
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'historique: {e}")