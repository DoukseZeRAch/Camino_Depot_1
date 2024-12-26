# backend/tests/test_openai_connection.py

import os
import sys

# Ajouter le chemin de base du projet au PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

# Configurer les paramètres Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')

import django
django.setup()

from apps.roadmap_management.services.ai_service import OpenAIConnection

def test_openai_connection():
    """
    Test pour valider la connexion à l'API OpenAI.
    """
    try:
        connection = OpenAIConnection()
        if connection.validate_connection():
            print("Connexion validée avec succès.")
        else:
            print("Échec de la validation de la connexion.")
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    test_openai_connection()
