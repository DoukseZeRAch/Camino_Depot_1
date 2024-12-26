# Nom du fichier : ai_preparation_service.py

from typing import Dict, Any, List, Optional
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.question_handling.models import Questions
from apps.user_management.models import Users
from apps.response_management.services.response_validation import ResponseValidator
import logging

logger = logging.getLogger(__name__)

class AIDataPreparationService:
    """
    Service complet de préparation des données pour l'IA.
    Gère la collecte des données utilisateur, leur structuration, et leur préparation pour utilisation par des services externes.
    """

    def __init__(self, model: str = "gpt-4", max_tokens: int = 4096):
        self.validator = ResponseValidator()
        self.model = model
        self.max_tokens = max_tokens

    async def prepare_complete_generation_data(
        self,
        temp_responses: Dict[str, Any],
        user: Users
    ) -> Dict[str, Any]:
        """
        Prépare les données complètes pour la génération et construit le prompt final.
        """
        try:
            structured_data = await self._prepare_full_data(temp_responses, user)

            # Analyse du contexte (anciennement AIPromptService)
            context_analysis = self._analyze_context(structured_data)

            # Construction du prompt validé
            prompt = await self._build_validated_prompt(structured_data, context_analysis)

            return {
                "data": structured_data,
                "prompt": prompt,
                "context_analysis": context_analysis
            }

        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données AI: {str(e)}")
            raise ValidationError("Échec de la préparation des données pour l'IA.")

    async def _prepare_full_data(self, temp_responses: Dict[str, Any], user: Users) -> Dict[str, Any]:
        """
        Prépare les données structurées nécessaires pour l'IA.
        """
        questions = await self._get_all_questions()

        structured_data = {
            "user_info": await self._prepare_user_info(user),
            "questionnaire_context": self._prepare_questionnaire_context(questions),
            "user_responses": [],
            "unanswered_questions": [],
            "metadata": {
                "total_questions": len(questions),
                "answered_questions": len(temp_responses),
                "categories": set(),
                "user_context": await self._prepare_user_context(user)
            }
        }

        await self._process_questions_and_responses(questions, temp_responses, structured_data)
        self._finalize_preparation(structured_data)

        return structured_data

    async def _get_all_questions(self) -> List[Questions]:
        """
        Récupère toutes les questions actives de manière asynchrone.
        """
        return await Questions.objects.filter(is_active=True).order_by('order_num').async_all()

    async def _prepare_user_info(self, user: Users) -> Dict[str, Any]:
        """
        Prépare les informations utilisateur.
        """
        roadmaps_count = await user.roadmaps.acount() if hasattr(user, 'roadmaps') else 0

        return {
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "profile": {
                "roadmaps_generated": roadmaps_count,
                "last_activity": user.last_login.isoformat() if user.last_login else None,
                "is_active": user.is_active
            }
        }

    async def _prepare_user_context(self, user: Users) -> Dict[str, Any]:
        """
        Prépare le contexte utilisateur avancé.
        """
        return {
            "experience_duration": self._calculate_experience_duration(user.created_at),
            "activity_level": await self._calculate_activity_level(user)
        }

    def _calculate_experience_duration(self, created_at: timezone.datetime) -> str:
        """
        Calcule la durée d'expérience de l'utilisateur.
        """
        duration = timezone.now() - created_at
        days = duration.days
        return f"{days} jours" if days < 30 else f"{days // 30} mois" if days < 365 else f"{days // 365} ans"

    async def _calculate_activity_level(self, user: Users) -> str:
        """
        Calcule le niveau d'activité de l'utilisateur.
        """
        last_activity = timezone.now() - user.last_login if user.last_login else None
        if last_activity and last_activity.days < 7:
            return "Très actif"
        elif last_activity and last_activity.days < 30:
            return "Actif"
        else:
            return "Inactif"

    def _prepare_questionnaire_context(self, questions: List[Questions]) -> Dict[str, Any]:
        """
        Prépare le contexte des questions.
        """
        return {
            "total_questions": len(questions),
            "categories": list({q.category for q in questions if q.category})
        }

    async def _process_questions_and_responses(self, questions: List[Questions], temp_responses: Dict[str, Any], structured_data: Dict[str, Any]) -> None:
        """
        Traite les questions et les réponses utilisateur.
        """
        for question in questions:
            response = temp_responses.get(str(question.id))
            if response:
                self.validator.validate_response(question.type, response, question.configuration)
                structured_data["user_responses"].append({
                    "question_id": str(question.id),
                    "answer": response
                })
            else:
                structured_data["unanswered_questions"].append({"question_id": str(question.id)})

    def _finalize_preparation(self, structured_data: Dict[str, Any]) -> None:
        """
        Finalise la préparation des données structurées.
        """
        structured_data["metadata"]["completion_rate"] = len(structured_data["user_responses"]) / structured_data["metadata"]["total_questions"] * 100

    async def _build_validated_prompt(self, structured_data: Dict[str, Any], context_analysis: Dict[str, Any]) -> str:
        """
        Construit et valide le prompt final.
        """
        return f"Prompt basé sur {structured_data['user_info']['username']}."

    def _analyze_context(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse le contexte pour ajuster les paramètres.
        """
        return {"key_themes": [], "priority_areas": []}
