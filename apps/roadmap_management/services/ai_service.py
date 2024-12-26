# backend/apps/roadmap_management/services/ai_service.py

from openai import OpenAI, OpenAIError, AzureOpenAI
from typing import Dict, Any, Optional, TYPE_CHECKING, List
import logging
from django.conf import settings
import time
from datetime import datetime
from .ai_preparation_service import AIDataPreparationService
from django.utils import timezone
from django.core.exceptions import ValidationError 
if TYPE_CHECKING:
    from roadmap_management.services.ai_settings import AISettingsService
    from roadmap_management.models import Roadmaps
    from apps.user_management.models import Users
    
logger = logging.getLogger(__name__)

class OpenAIClientError(Exception):
    """Erreur lors de l'initialisation du client OpenAI"""
    pass

class OpenAIRequestError(Exception):
    """Erreur lors de l'envoi d'une requête à l'API"""
    pass

class AIService:
    """Service pour gérer les interactions avec l'API OpenAI."""

    def __init__(self, settings_service: Optional['AISettingsService'] = None):
        """Initialise le service avec le bon client selon la configuration."""
        self.settings_service = settings_service
        
        try:
            if getattr(settings, 'OPENAI_API_TYPE', 'openai') == 'azure':
                self.client = self._init_azure_client()
            else:
                self.client = self._init_openai_client()
        except Exception as e:
            logger.error(f"Erreur d'initialisation du client OpenAI: {str(e)}")
            raise OpenAIClientError(f"Impossible d'initialiser le client OpenAI: {str(e)}")
        
    def _init_openai_client(self) -> OpenAI:
        """Initialise un client OpenAI standard."""
        if not settings.OPENAI_API_KEY:
            raise OpenAIClientError("Clé API OpenAI manquante")
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def _init_azure_client(self) -> AzureOpenAI:
        """Initialise un client Azure OpenAI."""
        if not all([
            settings.OPENAI_API_KEY,
            settings.AZURE_OPENAI_ENDPOINT,
            settings.AZURE_OPENAI_API_VERSION
        ]):
            raise OpenAIClientError("Configuration Azure OpenAI incomplète")
            
        return AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )

    async def generate_completion(
        self,
        messages: list[dict[str, str]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envoie une requête de complétion à l'API OpenAI.
        
        Args:
            messages: Liste de messages au format OpenAI
            config: Configuration de la requête (modèle, température, etc.)
            
        Returns:
            Dictionnaire contenant la réponse et les métadonnées
            
        Raises:
            OpenAIRequestError: En cas d'erreur lors de la requête
        """
        try:
            start_time = time.time()
            
            response = await self.client.chat.completions.create(
                model=config['model'],
                messages=messages,
                temperature=config['temperature'],
                max_tokens=config['max_tokens'],
                presence_penalty=config.get('presence_penalty', 0),
                frequency_penalty=config.get('frequency_penalty', 0)
            )
            
            generation_time = time.time() - start_time
            
            return {
                'content': response.choices[0].message.content,
                'token_count': response.usage.total_tokens,
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'model': config['model'],
                'generation_time': generation_time,
                'finish_reason': response.choices[0].finish_reason,
                'timestamp': datetime.now().isoformat()
            }
            
        except OpenAIError as e:
            logger.error(f"Erreur API OpenAI: {str(e)}")
            raise OpenAIRequestError(f"Erreur lors de la requête OpenAI: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur inattendue: {str(e)}")
            raise OpenAIRequestError(f"Erreur inattendue lors de la requête: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Vérifie l'état de la connexion à l'API.
        
        Returns:
            Dict contenant le statut de la connexion
            
        Raises:
            OpenAIRequestError: En cas d'échec du test
        """
        try:
            await self.generate_completion(
                messages=[{"role": "user", "content": "Test"}],
                config={
                    'model': 'gpt-3.5-turbo',
                    'temperature': 0.7,
                    'max_tokens': 5
                }
            )
            
            return {
                'status': 'healthy',
                'api_connected': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Échec du health check: {str(e)}")
            return {
                'status': 'unhealthy',
                'api_connected': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
class RoadmapAIService:
    """Service pour la génération de roadmaps utilisant l'IA."""

    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        settings_service: Optional['AISettingsService'] = None,
        data_service: Optional[AIDataPreparationService] = None
    ):
        self.ai_service = ai_service or AIService(settings_service)
        self.settings_service = settings_service
        self.data_service = data_service or AIDataPreparationService()

    async def generate_roadmap(
        self,
        prompt: str,
        structured_data: Dict[str, Any],
        **config_kwargs: Any
    ) -> Dict[str, Any]:
        """
        Génère une roadmap à partir d'un prompt et des données structurées.
        
        Args:
            prompt: Prompt préparé
            structured_data: Données structurées
            **config_kwargs: Configuration optionnelle pour l'IA
            
        Returns:
            Dict contenant le contenu généré et les métadonnées
        """
        try:
            # Préparation de la configuration
            config = await self._prepare_generation_config(
                structured_data,
                config_kwargs
            )
            
            # Création des messages pour l'API
            messages = self._create_messages(prompt)
            
            # Génération via l'API
            start_time = time.time()
            response = await self.ai_service.generate_completion(
                messages=messages,
                config=config
            )
            
            return {
                "content": response["content"],
                "metadata": {
                    "model": response["model"],
                    "token_count": response["token_count"],
                    "generation_time": response["generation_time"],
                    "finish_reason": response["finish_reason"]
                }
            }

        except Exception as e:
            logger.error(f"Erreur génération roadmap: {str(e)}")
            raise ValidationError(f"Erreur génération roadmap: {str(e)}")

    async def _prepare_generation_config(
        self,
        structured_data: Dict[str, Any],
        config_override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prépare la configuration pour la génération.
        
        Args:
            structured_data: Données structurées
            config_override: Configuration personnalisée
            
        Returns:
            Configuration finale
        """
        # Configuration de base
        base_config = self.settings_service.get_default_configuration()
        
        # Ajustements basés sur l'analyse technique
        technical_score = structured_data.get("technical_score", 0.5)
        base_config["temperature"] = max(0.3, 1 - technical_score)
        
        # Application des overrides
        final_config = {**base_config, **config_override}
        
        # Validation
        return self.settings_service.validate_configuration(final_config)

    def _create_messages(self, prompt: str) -> List[Dict[str, str]]:
        """
        Crée la liste des messages pour l'API.
        
        Args:
            prompt: Prompt principal
            
        Returns:
            Liste de messages formatés pour l'API
        """
        return [
            {
                "role": "system",
                "content": "Tu es un expert en création de roadmaps personnalisées..."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

    async def analyze_context(
        self,
        structured_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyse le contexte pour ajuster les paramètres.
        
        Args:
            structured_data: Données structurées
            
        Returns:
            Résultats de l'analyse et suggestions
        """
        try:
            # Analyse des réponses
            responses = structured_data.get('user_responses', [])
            technical_terms = [
                'code', 'programming', 'development', 'technical',
                'engineering', 'software', 'algorithm'
            ]
            
            technical_count = sum(
                1 for resp in responses
                if any(term in str(resp.get('answer', '')).lower()
                for term in technical_terms)
            )
            
            technical_precision = technical_count / len(responses) if responses else 0
            
            return {
                'technical_precision': technical_precision,
                'response_complexity': len(responses),
                'suggested_temperature': max(0.3, 1 - technical_precision)
            }
            
        except Exception as e:
            logger.warning(f"Erreur analyse du contexte: {e}")
            return {
                'technical_precision': 0.5,
                'response_complexity': 0,
                'suggested_temperature': 0.7
            }

    async def log_generation(
        self,
        roadmap: 'Roadmaps',
        prompt: str,
        response: Dict[str, Any],
        config: Dict[str, Any],
        start_time: float
    ) -> None:
        """
        Enregistre les détails de la génération.
        
        Args:
            roadmap: Instance de la roadmap
            prompt: Prompt utilisé
            response: Réponse de l'API
            config: Configuration utilisée
            start_time: Timestamp de début
        """
        if self.settings_service:
            await self.settings_service.log_generation(
                roadmap=roadmap,
                configuration=config,
                prompt=prompt,
                token_count=response["token_count"],
                start_time=start_time,
                success=True
            )