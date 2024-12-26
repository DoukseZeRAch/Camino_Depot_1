# backend/apps/question_handling/models.py
from django.db import models
from apps.user_management.models import Users
from django.core.exceptions import ValidationError
import uuid


# Modèle Questions
class Questions(models.Model):
    QUESTION_TYPES = [
        ('TEXT', 'Text'),
        ('MULTIPLE_CHOICE', 'Multiple Choice'),
        ('TABLE', 'Table')
    ]
    id = models.UUIDField(primary_key=True, default= uuid.uuid4, editable=False)
    text = models.CharField(max_length=255, blank=True, null=True,  unique=True)
    type = models.CharField(
        max_length=50,
        choices=QUESTION_TYPES,
        blank=True, 
        null=True
    )
    category = models.CharField(max_length=50, blank=True, null=True)
    order_num = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    configuration = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey('user_management.Users', on_delete=models.PROTECT, db_column='created_by', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'questions'
    def clean(self):
        self._validate_configuration()

    def _validate_configuration(self):
        
        if not isinstance(self.configuration, dict):
            raise ValidationError("Configuration must be a valid JSON object (dictionary)")
        if self.type == 'MULTIPLE_CHOICE' and self.configuration:
            options = self.configuration.get('options', [])
            if not isinstance(options, list):
               raise ValidationError("Options must be a list")
            if len(options) > 5:
                raise ValidationError("Maximum 5 options allowed")
        elif self.type == 'TABLE' and self.configuration:
            columns = self.configuration.get('columns', [])
            if not isinstance(columns, list):
                raise ValidationError("Columns must be a list")
            if len(columns) > 3:
                raise ValidationError("Maximum 3 columns allowed")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
