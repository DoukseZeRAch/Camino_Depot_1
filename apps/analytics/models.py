# apps/analytics/models.py
from django.db import models
from django.utils import timezone

class AnalyticsCache(models.Model):
    """
    Modèle pour mettre en cache les résultats d'analyses fréquemment demandées
    """
    CACHE_TYPES = [
        ('QUESTIONS', 'Questions Statistics'),
        ('RESPONSES', 'Responses Statistics'),
        ('ROADMAPS', 'Roadmaps Statistics'),
        ('USERS', 'Users Statistics'),
        ('DASHBOARD', 'Dashboard Overview')
    ]

    key = models.CharField(max_length=255, unique=True)
    cache_type = models.CharField(max_length=20, choices=CACHE_TYPES)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    parameters = models.JSONField(null=True, blank=True, 
                                help_text="Parameters used to generate this cache")

    class Meta:
        db_table = 'analytics_cache'
        indexes = [
            models.Index(fields=['cache_type', 'expires_at']),
            models.Index(fields=['key']),
        ]

    @property
    def is_valid(self):
        return self.expires_at > timezone.now()

# Create your models here.
