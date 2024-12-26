# apps/roadmap_management/services/prompt_validation_service.py

from __future__ import annotations
from typing import Dict, Any, Set, Optional, List, TYPE_CHECKING
from django.core.exceptions import ValidationError
import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class VariableType(Enum):
    """Types de variables supportés dans les templates"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

@dataclass
class VariableDefinition:
    """Définition d'une variable de template"""
    name: str
    type: VariableType
    required: bool = True
    description: str = ""
    default: Any = None
    nested_fields: Optional[List[str]] = None

class PromptValidationError(ValidationError):
    """Exception personnalisée pour les erreurs de validation de prompt"""
    pass

class PromptValidationService:
    """Service de validation des prompts et leurs variables"""

    # Configuration des variables autorisées
    ALLOWED_VARIABLES = {
        'user': VariableDefinition(
            name='user',
            type=VariableType.OBJECT,
            required=True,
            description='Informations utilisateur',
            nested_fields=['username', 'role']
        ),
        'questions': VariableDefinition(
            name='questions',
            type=VariableType.ARRAY,
            required=True,
            description='Questions posées',
            nested_fields=['text', 'type']
        ),
        'responses': VariableDefinition(
            name='responses',
            type=VariableType.ARRAY,
            required=True,
            description='Réponses utilisateur',
            nested_fields=['content', 'is_valid']
        ),
        'context': VariableDefinition(
            name='context',
            type=VariableType.OBJECT,
            required=False,
            description='Contexte additionnel'
        ),
        'metadata': VariableDefinition(
            name='metadata',
            type=VariableType.OBJECT,
            required=False,
            description='Métadonnées de génération'
        )
    }

    @classmethod
    def validate_prompt_template(cls, template_content: str) -> Dict[str, Set[str]]:
        """
        Valide un template de prompt et retourne les variables utilisées.
        
        Args:
            template_content: Le contenu du template à valider
            
        Returns:
            Dict des variables trouvées et leurs champs
            
        Raises:
            PromptValidationError si le template n'est pas valide
        """
        try:
            # Extraction des variables
            variables = cls._extract_variables(template_content)
            
            # Validation des variables trouvées
            cls._validate_variables(variables)
            
            # Vérification des champs requis
            cls._validate_required_fields(variables)
            
            return variables
            
        except Exception as e:
            logger.error(f"Erreur validation template: {str(e)}")
            raise PromptValidationError(f"Template invalide: {str(e)}")

    @classmethod
    def validate_variables_data(
        cls, 
        variables: Dict[str, Set[str]], 
        data: Dict[str, Any]
    ) -> None:
        """
        Valide que les données correspondent aux variables attendues.
        
        Args:
            variables: Dict des variables et leurs champs attendus
            data: Données à valider
            
        Raises:
            PromptValidationError si les données ne sont pas valides
        """
        try:
            for var_name, fields in variables.items():
                # Vérification présence variable
                if var_name not in data:
                    if cls.ALLOWED_VARIABLES[var_name].required:
                        raise PromptValidationError(f"Variable requise manquante: {var_name}")
                    continue
                
                var_data = data[var_name]
                var_def = cls.ALLOWED_VARIABLES[var_name]
                
                # Validation du type
                cls._validate_variable_type(var_name, var_data, var_def.type)
                
                # Validation des champs
                if var_def.nested_fields:
                    cls._validate_nested_fields(var_name, var_data, fields, var_def)

        except PromptValidationError:
            raise
        except Exception as e:
            logger.error(f"Erreur validation données: {str(e)}")
            raise PromptValidationError(f"Données invalides: {str(e)}")

    @classmethod
    def substitute_variables(
        cls,
        template: str,
        data: Dict[str, Any],
        safe_mode: bool = True
    ) -> str:
        """
        Remplace les variables dans le template par leurs valeurs.
        
        Args:
            template: Le template avec variables
            data: Les données pour les variables
            safe_mode: Si True, vérifie les données avant substitution
            
        Returns:
            Le template avec les variables remplacées
            
        Raises:
            PromptValidationError en cas d'erreur
        """
        try:
            if safe_mode:
                variables = cls._extract_variables(template)
                cls.validate_variables_data(variables, data)

            result = template

            # Substitution des variables
            for var_name, var_data in data.items():
                if isinstance(var_data, (list, tuple)):
                    result = cls._substitute_array(result, var_name, var_data)
                elif isinstance(var_data, dict):
                    result = cls._substitute_object(result, var_name, var_data)
                else:
                    result = cls._substitute_simple(result, var_name, var_data)

            return result

        except Exception as e:
            logger.error(f"Erreur substitution: {str(e)}")
            raise PromptValidationError(f"Erreur substitution: {str(e)}")

    @classmethod
    def _extract_variables(cls, content: str) -> Dict[str, Set[str]]:
        """Extrait les variables et leurs champs du contenu"""
        variables: Dict[str, Set[str]] = {}
        
        # Regex pour capturer les variables avec leurs champs
        pattern = r'\{(\w+)(?:\.(\w+))?\}'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            var_name = match.group(1)
            field = match.group(2)
            
            if var_name not in cls.ALLOWED_VARIABLES:
                raise PromptValidationError(f"Variable non autorisée: {var_name}")
                
            if var_name not in variables:
                variables[var_name] = set()
                
            if field:
                variables[var_name].add(field)
                
        return variables

    @classmethod
    def _validate_variables(cls, variables: Dict[str, Set[str]]) -> None:
        """Valide les variables extraites"""
        for var_name in variables:
            if var_name not in cls.ALLOWED_VARIABLES:
                raise PromptValidationError(f"Variable non autorisée: {var_name}")

    @classmethod
    def _validate_required_fields(cls, variables: Dict[str, Set[str]]) -> None:
        """Vérifie la présence des champs requis"""
        for var_name, fields in variables.items():
            var_def = cls.ALLOWED_VARIABLES[var_name]
            if var_def.required and var_def.nested_fields:
                missing = set(var_def.nested_fields) - fields
                if missing:
                    raise PromptValidationError(
                        f"Champs requis manquants pour {var_name}: {missing}"
                    )

    @classmethod
    def _validate_variable_type(
        cls,
        var_name: str,
        value: Any,
        expected_type: VariableType
    ) -> None:
        """Valide le type d'une variable"""
        if expected_type == VariableType.ARRAY and not isinstance(value, (list, tuple)):
            raise PromptValidationError(f"{var_name} doit être un tableau")
            
        elif expected_type == VariableType.OBJECT and not isinstance(value, dict):
            raise PromptValidationError(f"{var_name} doit être un objet")
            
        elif expected_type == VariableType.NUMBER and not isinstance(value, (int, float)):
            raise PromptValidationError(f"{var_name} doit être un nombre")
            
        elif expected_type == VariableType.BOOLEAN and not isinstance(value, bool):
            raise PromptValidationError(f"{var_name} doit être un booléen")
            
        elif expected_type == VariableType.STRING and not isinstance(value, str):
            raise PromptValidationError(f"{var_name} doit être une chaîne")

    @classmethod
    def _validate_nested_fields(
        cls,
        var_name: str,
        data: Any,
        fields: Set[str],
        var_def: VariableDefinition
    ) -> None:
        """Valide les champs imbriqués"""
        if isinstance(data, (list, tuple)):
            for item in data:
                for field in fields:
                    if field not in item:
                        raise PromptValidationError(
                            f"Champ {field} manquant dans {var_name}"
                        )
        elif isinstance(data, dict):
            for field in fields:
                if field not in data:
                    raise PromptValidationError(
                        f"Champ {field} manquant dans {var_name}"
                    )

    @classmethod
    def _substitute_array(cls, template: str, var_name: str, values: List[Any]) -> str:
        """Remplace les variables de type tableau"""
        result = template
        for i, item in enumerate(values):
            for key in item:
                placeholder = f"{{{var_name}[{i}].{key}}}"
                result = result.replace(placeholder, str(item[key]))
        return result

    @classmethod
    def _substitute_object(cls, template: str, var_name: str, value: Dict[str, Any]) -> str:
        """Remplace les variables de type objet"""
        result = template
        for key in value:
            placeholder = f"{{{var_name}.{key}}}"
            result = result.replace(placeholder, str(value[key]))
        return result

    @classmethod
    def _substitute_simple(cls, template: str, var_name: str, value: Any) -> str:
        """Remplace les variables simples"""
        placeholder = f"{{{var_name}}}"
        return template.replace(placeholder, str(value))

    @classmethod
    def get_template_info(cls) -> Dict[str, Dict[str, Any]]:
        """
        Retourne les informations sur les variables disponibles.
        
        Returns:
            Dict avec les descriptions des variables
        """
        return {
            var_name: {
                'description': var_def.description,
                'type': var_def.type.value,
                'required': var_def.required,
                'nested_fields': var_def.nested_fields
            }
            for var_name, var_def in cls.ALLOWED_VARIABLES.items()
        }