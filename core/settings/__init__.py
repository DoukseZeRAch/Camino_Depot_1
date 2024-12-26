# backend/core/settings/__init__.py

import os

# Chargement des variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Définition du module de settings par défaut
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')