from typing import Dict, Any, List, Optional
import json
from django.core.exceptions import ValidationError
from tiktoken import encoding_for_model

class ResponseValidator:
    """Service de validation des réponses selon leur type"""

    @staticmethod
    def validate_text_response(content: str, config: Dict = None) -> bool:
        """Valide une réponse de type texte"""
        if not content or not isinstance(content, str):
            raise ValidationError("La réponse doit être une chaîne de caractères non vide")
        
        config = config or {}
        min_length = config.get('min_length', 0)
        max_length = config.get('max_length', 10000)
        max_tokens = config.get('max_tokens', 4096)
        
        if len(content) < min_length:
            raise ValidationError(f"La réponse doit contenir au moins {min_length} caractères")
        if len(content) > max_length:
            raise ValidationError(f"La réponse ne doit pas dépasser {max_length} caractères")
        if ResponseValidator.estimate_tokens(content) > max_tokens:
            raise ValidationError(f"Le contenu dépasse la limite de {max_tokens} tokens autorisés.")
        
        return True

    @staticmethod
    def validate_multiple_choice_response(selected_options: List, config: Dict) -> bool:
        """Valide une réponse à choix multiples"""
        if not isinstance(selected_options, list):
            raise ValidationError("Les options sélectionnées doivent être une liste")
        
        available_options = config.get('options', [])
        allow_multiple = config.get('allow_multiple', False)
        min_selections = config.get('min_selections', 1)
        max_selections = config.get('max_selections', len(available_options))
        
        # Vérifier que toutes les options sélectionnées sont valides
        for option in selected_options:
            if option not in available_options:
                raise ValidationError(f"Option invalide : {option}")
        
        # Vérifier le nombre de sélections
        if not allow_multiple and len(selected_options) > 1:
            raise ValidationError("Une seule option peut être sélectionnée")
        if len(selected_options) < min_selections:
            raise ValidationError(f"Minimum {min_selections} option(s) requise(s)")
        if len(selected_options) > max_selections:
            raise ValidationError(f"Maximum {max_selections} option(s) autorisée(s)")
        
        return True

    @staticmethod
    def validate_table_response(rows: List[Dict], config: Dict) -> bool:
        """Valide une réponse de type tableau"""
        if not isinstance(rows, list):
            raise ValidationError("Les données du tableau doivent être une liste")
        
        columns = config.get('columns', [])
        min_rows = config.get('min_rows', 0)
        max_rows = config.get('max_rows', 100)
        
        if len(rows) < min_rows:
            raise ValidationError(f"Minimum {min_rows} ligne(s) requise(s)")
        if len(rows) > max_rows:
            raise ValidationError(f"Maximum {max_rows} ligne(s) autorisée(s)")
        
        # Vérifier chaque ligne
        for row in rows:
            if not isinstance(row, dict):
                raise ValidationError("Chaque ligne doit être un dictionnaire")
            
            # Vérifier les colonnes requises
            for column in columns:
                if column.get('required', False) and column['name'] not in row:
                    raise ValidationError(f"Colonne requise manquante : {column['name']}")
                
                # Valider le type de données si spécifié
                if column['name'] in row and 'data_type' in column:
                    ResponseValidator._validate_data_type(
                        row[column['name']], 
                        column['data_type'],
                        column['name']
                    )
        
        return True

    @staticmethod
    def _validate_data_type(value: Any, expected_type: str, field_name: str) -> None:
        """Valide le type de données d'une valeur"""
        type_mapping = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool
        }
        
        if expected_type in type_mapping:
            try:
                if not isinstance(value, type_mapping[expected_type]):
                    # Tentative de conversion
                    type_mapping[expected_type](value)
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Type de données invalide pour {field_name}. Attendu : {expected_type}"
                )

    @staticmethod
    def estimate_tokens(content: str, model="gpt-4") -> int:
        """Estime le nombre de tokens pour une chaîne de caractères donnée"""
        try:
            encoding = encoding_for_model(model)
            return len(encoding.encode(content))
        except Exception as e:
            raise ValidationError(f"Erreur lors de l'estimation des tokens : {e}")

    def validate_response(self, question_type: str, content: Any, config: Dict = None) -> bool:
        """Point d'entrée principal pour la validation des réponses"""
        validation_methods = {
            'TEXT': self.validate_text_response,
            'MULTIPLE_CHOICE': self.validate_multiple_choice_response,
            'TABLE': self.validate_table_response
        }
        
        if question_type not in validation_methods:
            raise ValidationError(f"Type de question non supporté : {question_type}")
            
        return validation_methods[question_type](content, config or {})
