from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
import uuid
import logging
from django.utils import timezone  

from apps.response_management.models import ResponsesBackup

logger = logging.getLogger(__name__)

class Users(AbstractUser):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    email = models.CharField(unique=True, max_length=255, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(
        max_length=7,
        choices=[
            ('USER', 'User'),
            ('MANAGER', 'Manager'),
            ('ADMIN', 'Admin')
        ],
        default='USER'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    is_authenticated = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        swappable = 'AUTH_USER_MODEL'
    # Dans models.py de Users
def delete(self, deleted_by=None, self_delete=False, *args, **kwargs):
    """
    Suppression d'un utilisateur avec vérifications et traçabilité
    Args:
        deleted_by: L'utilisateur qui effectue la suppression
        self_delete: Boolean indiquant si l'utilisateur supprime son propre compte
    """
    if not self_delete and not deleted_by:
        raise ValueError("Préciser soit self_delete=True, soit l'utilisateur effectuant la suppression")

    if not self_delete:
        # Cas 1: Suppression par admin/manager
        if deleted_by.role not in ['ADMIN', 'MANAGER']:
            raise PermissionError("Seuls les admins et managers peuvent supprimer des utilisateurs")
        deleter_info = f"par {deleted_by.email} ({deleted_by.role})"
    else:
        # Cas 2: Auto-suppression
        if deleted_by and deleted_by.id != self.id:
            raise PermissionError("Un utilisateur ne peut supprimer que son propre compte")
        deleter_info = "par l'utilisateur lui-même"

    try:
        with transaction.atomic():
            # 1. Sauvegarde de l'information
            user_info = {
                'id': self.id,
                'email': self.email,
                'role': self.role,
                'deleted_by': deleter_info,
                'deleted_at': timezone.now()
            }

            # 2. Gestion des réponses et backups
            responses = self.responses.all()
            original_responses = responses.filter(is_original=True)
            
            if original_responses.exists():
                # Création des backups finaux
                for response in original_responses:
                    ResponsesBackup.objects.create(
                        response=response,
                        user=self,
                        question=response.question,
                        content=response.content,
                        is_complete=response.is_complete,
                        version_index=response.backups.count() + 1
                    )
                
                # Désactivation du flag is_original
                original_responses.update(is_original=False)

            # 3. Suppression en cascade
            super().delete(*args, **kwargs)

            # 4. Log de l'opération
            print(f"Utilisateur {self.email} supprimé {deleter_info}")
            print(f"Détails de la suppression: {user_info}")

    except Exception as e:
        print(f"Erreur lors de la suppression de l'utilisateur {self.email}: {str(e)}")
        raise