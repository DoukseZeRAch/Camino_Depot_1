# Nom du fichier : ai_prompt_service.py

from __future__ import annotations
from typing import Dict, Any, List
from django.core.exceptions import ValidationError
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PreparationConfig:
    """Configuration pour la préparation des données"""
    include_history: bool = True
    max_history_items: int = 10
    include_metadata: bool = True
    technical_analysis: bool = True

    def __post_init__(self):
        """Valide la configuration après initialisation"""
        if self.max_history_items <= 0:
            raise ValidationError("max_history_items doit être positif.")

class AIPromptService:
    """
    Service de gestion des prompts pour l'IA.
    Responsable de la création, validation, et gestion des templates de prompts.
    """

    def __init__(self, model: str = "gpt-4", max_tokens: int = 4096):
        self.model = model
        self.max_tokens = max_tokens
        self.config = PreparationConfig()

    def generate_prompt(self, structured_data: Dict[str, Any]) -> str:
        """
        Génère un prompt à partir des données structurées.
        """
        try:
            user_info = structured_data.get("user_info", {})
            user_name = user_info.get("username", "Utilisateur inconnu")
            metadata = structured_data.get("metadata", {})
            categories = metadata.get("categories", [])

            prompt = (
                f"Bonjour {user_name},\n"
                f"Voici les catégories disponibles : {', '.join(categories)}.\n"
                f"Merci de fournir des réponses détaillées pour chaque section."
            )
            return prompt

        except Exception as e:
            logger.error(f"Erreur lors de la génération du prompt : {e}")
            raise ValidationError("Erreur dans la génération du prompt.")

    def validate_prompt_template(self, template: str) -> None:
        """
        Valide un template de prompt.
        """
        required_variables = ["{user_info}", "{categories}"]
        for var in required_variables:
            if var not in template:
                raise ValidationError(f"Le template doit contenir {var}.")
        logger.info("Template validé avec succès.")
        
    def substitute_variables(self, template: str, data: Dict[str, Any]) -> str:
        """
        Remplace les variables dans un template avec les données fournies.
        """
        try:
            user_info = data.get("user_info", {})
            categories = data.get("metadata", {}).get("categories", [])
            answers = data.get("answers", [])

            filled_template = template.format(
                user_info=user_info.get("username", "Utilisateur inconnu"),
                categories=", ".join(categories),
                answers="\n".join(answers),
            )
            logger.info("Template substitué avec succès.")
            return filled_template

        except KeyError as e:
            logger.error(f"Erreur lors de la substitution des variables : {e}")
            raise ValidationError(f"Variable manquante : {e}")

    def adjust_parameters(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ajuste les paramètres en fonction des données structurées.
        """
        metadata = structured_data.get("metadata", {})
        total_questions = metadata.get("total_questions", 1)
        answered_questions = metadata.get("answered_questions", 0)

        completion_rate = answered_questions / total_questions if total_questions else 0
        temperature = 0.7 if completion_rate > 0.8 else 0.9

        return {"temperature": temperature, "max_tokens": self.max_tokens}
    

    def log_prompt_generation(self, prompt: str, user_info: Dict[str, Any]) -> None:
        """
        Enregistre les détails de la génération de prompt.
        """
        logger.info(f"Prompt généré pour {user_info.get('username', 'inconnu')}: {prompt[:100]}...")
