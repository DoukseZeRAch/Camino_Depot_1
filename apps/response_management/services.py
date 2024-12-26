# apps/response_management/services.py

from .models import Responses
from apps.question_handling.models import Questions
from django.db import transaction

class ResponseService:
    @staticmethod
    @transaction.atomic
    def correct_table_responses(project_question_id, exp_question_id):
        """
        Corrige les réponses aux questions table inversées
        """
        try:
            # Récupérer les questions
            project_question = Questions.objects.get(id=project_question_id)
            exp_question = Questions.objects.get(id=exp_question_id)

            # Récupérer les réponses
            project_response = Responses.objects.get(question=project_question)
            exp_response = Responses.objects.get(question=exp_question)

            # Vérifier que ce sont des questions de type TABLE
            if project_question.type != 'TABLE' or exp_question.type != 'TABLE':
                raise ValueError("Les questions doivent être de type TABLE")

            # Sauvegarder les contenus temporairement
            temp_content = project_response.content
            temp_complete = project_response.is_complete

            # Échanger les contenus
            project_response.content = exp_response.content
            project_response.is_complete = exp_response.is_complete
            project_response.save()

            exp_response.content = temp_content
            exp_response.is_complete = temp_complete
            exp_response.save()

            return True, "Réponses corrigées avec succès"

        except Exception as e:
            return False, f"Erreur lors de la correction: {str(e)}"

    @staticmethod
    def validate_all_table_responses():
        """
        Valide toutes les réponses de type TABLE
        """
        table_responses = Responses.objects.filter(question__type='TABLE')
        errors = []

        for response in table_responses:
            try:
                response.validate_table_response()
            except ValidationError as e:
                errors.append({
                    'response_id': response.id,
                    'error': str(e)
                })

        return errors