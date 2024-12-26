# backend/apps/response_management/models.py
from django.db import models
import uuid
import logging
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.db import transaction

logger = logging.getLogger(__name__)

class Responses(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'user_management.Users', 
        on_delete=models.CASCADE,
        related_name='responses'
    )
    question = models.ForeignKey('question_handling.Questions', on_delete=models.CASCADE, db_column='question_id', blank=True, null=True)
    content = models.JSONField(blank=True, null=True)
    is_valid = models.BooleanField(default=False)
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    draft_data = models.JSONField(blank=True, null=True)
    is_original = models.BooleanField(default=False)

    class Meta:
        db_table = 'responses'

    def save(self, *args, **kwargs):
        force_insert = kwargs.pop('force_insert', False)
        token = kwargs.pop('token', None)

        # Si force_insert est True, c'est une nouvelle création forcée
        if force_insert:
            self.is_original = True
            return super().save(*args, **kwargs)

        try:
            # Vérifier si une réponse existe déjà pour cet utilisateur et cette question
            existing_response = Responses.objects.filter(
                user=self.user, 
                question=self.question
            ).first()

            if existing_response:
                # Créer un backup de la réponse existante
                ResponsesBackup.objects.create(
                    response=existing_response,
                    user=existing_response.user,
                    question=existing_response.question,
                    content=existing_response.content,
                    is_complete=existing_response.is_complete,
                    connection_token=token,
                    version_index=existing_response.backups.count() + 1
                )
                
                # Mettre à jour la réponse existante
                existing_response.content = self.content
                existing_response.is_complete = self.is_complete
                existing_response.draft_data = self.draft_data
                existing_response.is_valid = self.is_valid
                existing_response.save(update_fields=['content', 'is_complete', 'draft_data', 'is_valid', 'updated_at'])
                return existing_response
            else:
                # Première réponse pour cette question
                self.is_original = True
                return super().save(*args, **kwargs)
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la réponse: {str(e)}")
            raise

    def delete(self, *args, force_delete=False, **kwargs):
        """
        Méthode de suppression avec protection de la réponse originale
        
        Args:
            force_delete (bool): Si True, permet la suppression même si is_original=True 
                               (utilisé uniquement lors de la suppression de l'utilisateur)
        """
        if self.is_original and not force_delete:
            raise ValidationError("Impossible de supprimer la réponse originale")
        super().delete(*args, **kwargs)

    def validate_response(self):
        """Valide la réponse selon son type"""
        if not self.question or not self.content:
            self.is_valid = False
            return False

        try:
            if self.question.type == 'MULTIPLE_CHOICE':
                valid_options = self.question.configuration.get('options', [])
                selected_options = self.content.get('selected', [])
                self.is_valid = all(option in valid_options for option in selected_options)

            elif self.question.type == 'TABLE':
                if not self.validate_table_response():
                    self.is_valid = False
                    return False
                rows = self.content.get('rows', [])
                self.is_valid = all(all(value for value in row.values()) for row in rows)

            elif self.question.type == 'TEXT':
                text = self.content.get('text', '').strip()
                min_length = self.question.configuration.get('min_length', 0)
                max_length = self.question.configuration.get('max_length', float('inf'))
                
                self.is_valid = bool(text) and min_length <= len(text) <= max_length

            else:
                self.is_valid = False

            self.save(update_fields=['is_valid', 'updated_at'])
            return self.is_valid

        except Exception as e:
            logger.error(f"Erreur lors de la validation de la réponse: {str(e)}")
            self.is_valid = False
            self.save(update_fields=['is_valid', 'updated_at'])
            return False

    def validate_table_response(self):
        """
        Valide que les colonnes de la réponse correspondent à la configuration de la question
        """
        try:
            if self.question.type == 'TABLE':
                expected_headers = self.question.configuration.get('headers', [])
                content_rows = self.content.get('rows', [])
                
                if not content_rows:
                    return False

                for row in content_rows:
                    if set(row.keys()) != set(expected_headers):
                        logger.error(
                            f"Erreur de format: colonnes {row.keys()} ne correspondent pas "
                            f"aux en-têtes attendus {expected_headers}"
                        )
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de la réponse table: {str(e)}")
            return False

class ResponsesBackup(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4, editable=False)
    response = models.ForeignKey('Responses', on_delete=models.CASCADE, related_name="backups")
    user = models.ForeignKey('user_management.Users', on_delete=models.CASCADE)
    question = models.ForeignKey('question_handling.Questions', on_delete=models.CASCADE)
    content = models.JSONField()
    is_complete = models.BooleanField(default=False)
    backup_at = models.DateTimeField(auto_now_add=True)
    connection_token = models.CharField(max_length=255, blank=True, null=True)
    version_index = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = 'responses_backup'
        ordering = ['backup_at']

@receiver(pre_delete, sender='user_management.Users')
def delete_user_responses(sender, instance, **kwargs):
    """
    Supprime toutes les réponses et backups associés à un utilisateur avant sa suppression.
    """
    try:
        with transaction.atomic():
            # Récupérer les réponses et backups
            responses = Responses.objects.filter(user=instance)
            backups = ResponsesBackup.objects.filter(user=instance)
            
            # Compter pour les logs
            response_count = responses.count()
            backup_count = backups.count()
            
            # Supprimer dans l'ordre correct avec force_delete pour les réponses
            backups.delete()
            for response in responses:
                response.delete(force_delete=True)
            
            logger.info(
                f"Suppression réussie pour l'utilisateur {instance.id}: "
                f"{response_count} réponses et {backup_count} backups supprimés."
            )
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des données de l'utilisateur {instance.id}: {str(e)}")