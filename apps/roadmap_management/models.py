from django.db import models
from apps.user_management.models import Users
import uuid
from django.utils import timezone
from django.db import models
import uuid
from django.utils import timezone
from typing import Dict, Any
from collections import Counter
from django.core.exceptions import ValidationError

class Roadmaps(models.Model):
    STATUSES = [
        ('DRAFT', 'Draft'),
        ('GENERATING', 'Generating'),
        ('COMPLETED', 'Completed'),
        ('ERROR', 'Error'),
        ('ARCHIVED', 'Archived')
    ]

    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('user_management.Users', related_name='roadmaps', on_delete=models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUSES, default='DRAFT')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roadmaps'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} (v{self.version}) - {self.status}"

    def can_generate(self) -> bool:
        """Vérifie si la roadmap peut être générée"""
        return self.status not in ['GENERATING', 'ARCHIVED']

    def can_delete(self) -> bool:
        """Vérifie si la roadmap peut être supprimée"""
        return self.status != 'ARCHIVED'

    def increment_version(self):
        """Incrémente la version de la roadmap"""
        self.version = (self.version or 0) + 1
        
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = str(uuid.uuid4())
        super().save(*args, **kwargs)

class AIConfiguration(models.Model):
    """Configuration IA associée à une génération de roadmap"""
    roadmap = models.ForeignKey(
        'Roadmaps',
        on_delete=models.CASCADE,
        related_name='ai_configs'
    )
    model = models.CharField(
        max_length=50,
        choices=[
            ("gpt-4", "GPT-4"),
            ("gpt-4-turbo", "GPT-4 Turbo"),
            ("gpt-3.5-turbo", "GPT-3.5 Turbo")
        ],
        default="gpt-4"
    )
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=4096)
    prompt_template = models.TextField()
    
    # Nouveaux champs de configuration avancée
    presence_penalty = models.FloatField(default=0.0)
    frequency_penalty = models.FloatField(default=0.0)
    top_p = models.FloatField(default=1.0)
    tech_analysis_enabled = models.BooleanField(default=True)
    context_window = models.IntegerField(default=4096)
    
    # Champs existants
    token_count = models.IntegerField(null=True, blank=True)
    generation_time = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'roadmap_ai_configurations'
        ordering = ['-created_at']
        
    def clean(self):
        """Validation des paramètres de configuration"""
        if not 0 <= self.temperature <= 1:
            raise ValidationError("La température doit être entre 0 et 1")
            
        if not 1000 <= self.max_tokens <= 32000:
            raise ValidationError("max_tokens doit être entre 1000 et 32000")
            
        if not -2.0 <= self.presence_penalty <= 2.0:
            raise ValidationError("presence_penalty doit être entre -2.0 et 2.0")
            
        if not -2.0 <= self.frequency_penalty <= 2.0:
            raise ValidationError("frequency_penalty doit être entre -2.0 et 2.0")
            
        if not 0 <= self.top_p <= 1:
            raise ValidationError("top_p doit être entre 0 et 1")
class GlobalAIConfiguration(models.Model):
    """Configuration IA globale pour l'application"""
    
    model = models.CharField(
        max_length=50,
        choices=[
            ("gpt-4", "GPT-4"),
            ("gpt-4-turbo", "GPT-4 Turbo"),
            ("gpt-3.5-turbo", "GPT-3.5 Turbo")
        ],
        default="gpt-4"
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="Valeur entre 0 et 1 pour contrôler la créativité"
    )
    max_tokens = models.IntegerField(
        default=4096,
        help_text="Nombre maximum de tokens pour la réponse"
    )
    system_prompt = models.TextField(
        help_text="Prompt système par défaut pour la génération",
        default="Tu es un expert en création de roadmaps personnalisées..."
    )
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(
        'user_management.Users',
        on_delete=models.SET_NULL,
        null=True,
        related_name='ai_config_modifications'
    )

    class Meta:
        verbose_name = "Configuration IA Globale"
        verbose_name_plural = "Configuration IA Globale"

    @classmethod
    def get_current(cls):
        config = cls.objects.first()
        if not config:
            config = cls.objects.create()
        return config
class PromptTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Nom du Template")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    template_content = models.TextField(verbose_name="Contenu du Template")
    is_active = models.BooleanField(default=False, verbose_name="Actif")
    
    # Nouveaux champs techniques
    token_count = models.IntegerField(null=True, blank=True, verbose_name="Nombre de Tokens")
    model_used = models.CharField(max_length=50, null=True, blank=True, verbose_name="Modèle Utilisé")
    generation_time = models.FloatField(null=True, blank=True, verbose_name="Temps de Génération")
    technical_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Score Technique"
    )
    error_logs = models.TextField(null=True, blank=True, verbose_name="Logs d'Erreurs")
    
    # Champs d'historique
    version = models.IntegerField(default=1, verbose_name="Version")
    version_timestamp = models.DateTimeField(auto_now=True, verbose_name="Date de Version")
    version_changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Changements de Version"
    )
    version_author = models.ForeignKey(
        'user_management.Users',
        on_delete=models.SET_NULL,
        null=True,
        related_name='template_versions',
        verbose_name="Auteur de la Version"
    )
    
    # Champs existants
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        verbose_name = "Template de Prompt"
        verbose_name_plural = "Templates de Prompt"

    def clean(self):
        """Validation du contenu du template et des paramètres techniques"""
        # Validation des variables obligatoires
        required_variables = ["{user}", "{questions}", "{responses}", "{generation_date}"]
        for variable in required_variables:
            if variable not in self.template_content:
                raise ValidationError(f"Variable obligatoire manquante : {variable}")
        
        # Validation des paramètres techniques
        if self.token_count is not None and self.token_count < 0:
            raise ValidationError("Le nombre de tokens ne peut pas être négatif")
        
        if self.generation_time is not None and self.generation_time < 0:
            raise ValidationError("Le temps de génération ne peut pas être négatif")
        
        if self.technical_score is not None and not 0 <= float(self.technical_score) <= 100:
            raise ValidationError("Le score technique doit être entre 0 et 100")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (v{self.version})"