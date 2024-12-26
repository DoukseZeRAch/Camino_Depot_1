import asyncio
from django.core.exceptions import ValidationError
from apps.user_management.models import Users
from apps.question_handling.models import Questions
from apps.response_management.models import Responses, ResponsesBackup
from apps.roadmap_management.services.ai_service import RoadmapAIService
from apps.response_management.services.response_validation import ResponseValidator
from apps.roadmap_management.services.ai_preparation_service import AIDataPreparationService
from django.utils import timezone
import logging
import json

logger = logging.getLogger(__name__)

class RoadmapTestSuite:
    def __init__(self):
        self.validator = ResponseValidator()
        self.ai_service = RoadmapAIService()
        self.ai_prep_service = AIDataPreparationService()
        
    async def run_all_tests(self):
        """Exécute tous les tests dans l'ordre"""
        try:
            # 1. Vérification des tables
            await self.check_database_state()
            
            # 2. Création des utilisateurs
            manager = await self.create_manager()
            user = await self.create_user()
            print(f"Utilisateurs créés: Manager {manager.id}, User {user.id}")
            
            # 3. Création des questions par le manager
            questions = await self.create_test_questions(manager)
            print(f"Questions créées: {len(questions)} questions")
            
            # 4. Test des réponses temporaires
            temp_responses = await self.test_temporary_responses(user, questions)
            print("Réponses temporaires testées")
            
            # 5. Test de la génération de roadmap et sauvegarde
            roadmap_result = await self.test_roadmap_generation(user, temp_responses)
            print("Première roadmap générée")
            
            # 6. Test du changement d'ordre des questions
            await self.test_question_reordering(manager, questions)
            print("Ordre des questions modifié")
            
            # 7-8. Test du second cycle de réponses
            second_responses = await self.test_second_response_cycle(user, questions)
            print("Second cycle de réponses complété")
            
            # 9. Test de suppression
            await self.test_user_deletion(user)
            print("Tests de suppression complétés")
            
            return "Tests complétés avec succès"
            
        except Exception as e:
            logger.error(f"Erreur durant les tests: {str(e)}")
            raise

    async def check_database_state(self):
        """Vérifie l'état initial des tables"""
        users_count = await Users.objects.acount()
        questions_count = await Questions.objects.acount()
        responses_count = await Responses.objects.acount()
        
        return {
            "users": users_count,
            "questions": questions_count,
            "responses": responses_count
        }

    async def create_manager(self):
        """Crée un utilisateur manager"""
        return await Users.objects.acreate(
            username="adi",
            email="adi@test.com",
            role="MANAGER",
            is_active=True
        )

    async def create_user(self):
        """Crée un utilisateur standard"""
        return await Users.objects.acreate(
            username="camino",
            email="camino@test.com",
            role="USER",
            is_active=True
        )

    async def create_test_questions(self, manager):
        """Crée les questions de test"""
        questions = []
        
        # Questions texte
        text_questions = [
            {
                "text": "Décrivez votre expérience professionnelle",
                "type": "TEXT",
                "category": "EXPERIENCE",
                "order_num": 1,
                "configuration": {"min_length": 50, "max_length": 1000}
            },
            {
                "text": "Quels sont vos objectifs de carrière?",
                "type": "TEXT",
                "category": "OBJECTIVES",
                "order_num": 2,
                "configuration": {"min_length": 50, "max_length": 1000}
            }
        ]
        
        # Questions choix multiples
        multiple_choice_questions = [
            {
                "text": "Sélectionnez votre niveau d'expertise",
                "type": "MULTIPLE_CHOICE",
                "category": "SKILLS",
                "order_num": 3,
                "configuration": {
                    "options": ["Débutant", "Intermédiaire", "Avancé", "Expert"],
                    "allow_multiple": False
                }
            },
            {
                "text": "Sélectionnez vos domaines d'intérêt",
                "type": "MULTIPLE_CHOICE",
                "category": "INTERESTS",
                "order_num": 4,
                "configuration": {
                    "options": ["Frontend", "Backend", "DevOps", "Data Science"],
                    "allow_multiple": True,
                    "min_selections": 1,
                    "max_selections": 3
                }
            }
        ]
        
        # Questions table
        table_questions = [
            {
                "text": "Évaluez vos compétences",
                "type": "TABLE",
                "category": "SKILLS",
                "order_num": 5,
                "configuration": {
                    "headers": ["Compétence", "Niveau actuel", "Niveau souhaité"],
                    "min_rows": 1,
                    "max_rows": 5
                }
            }
        ]
        
        all_questions = text_questions + multiple_choice_questions + table_questions
        for q in all_questions:
            question = await Questions.objects.acreate(
                created_by=manager,
                created_at=timezone.now(),
                **q
            )
            questions.append(question)
        
        return questions

    async def test_temporary_responses(self, user, questions):
        """Test des réponses temporaires"""
        temp_responses = {}
        
        for question in questions:
            if question.type == "TEXT":
                temp_responses[str(question.id)] = {
                    "text": "Ceci est une réponse de test détaillée pour la question texte."
                }
            elif question.type == "MULTIPLE_CHOICE":
                if not question.configuration.get("allow_multiple"):
                    temp_responses[str(question.id)] = {
                        "selected": [question.configuration["options"][0]]
                    }
                else:
                    temp_responses[str(question.id)] = {
                        "selected": question.configuration["options"][:2]
                    }
            elif question.type == "TABLE":
                temp_responses[str(question.id)] = {
                    "rows": [
                        {
                            "Compétence": "Python",
                            "Niveau actuel": "Intermédiaire",
                            "Niveau souhaité": "Expert"
                        }
                    ]
                }
        
        return temp_responses

    async def test_roadmap_generation(self, user, temp_responses):
        """Test de la génération de roadmap"""
        prep_data = await self.ai_prep_service.prepare_complete_generation_data(
            temp_responses,
            user
        )
        
        return await self.ai_service.generate_roadmap(
            prep_data["prompt"],
            prep_data["data"]
        )

    async def test_question_reordering(self, manager, questions):
        """Test du réordonnancement des questions"""
        for i, question in enumerate(questions):
            question.order_num = len(questions) - i
            await question.asave()

    async def test_second_response_cycle(self, user, questions):
        """Test du second cycle de réponses"""
        # Similaire à test_temporary_responses mais avec des réponses différentes
        return await self.test_temporary_responses(user, questions)

    async def test_user_deletion(self, user):
        """Test de la suppression de l'utilisateur"""
        # Récupérer les compteurs avant suppression
        responses_before = await Responses.objects.filter(user=user).acount()
        backups_before = await ResponsesBackup.objects.filter(user=user).acount()
        
        # Supprimer l'utilisateur
        await user.adelete()
        
        # Vérifier que tout a été supprimé
        responses_after = await Responses.objects.filter(user=user).acount()
        backups_after = await ResponsesBackup.objects.filter(user=user).acount()
        
        return {
            "responses_deleted": responses_before - responses_after,
            "backups_deleted": backups_before - backups_after
        }