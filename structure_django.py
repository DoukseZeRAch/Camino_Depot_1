import os
import sys
from pathlib import Path
import ast
import importlib.util
import inspect

# Ajout des chemins nécessaires au PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
APPS_DIR = BASE_DIR / 'apps'

# Ajout du dossier apps au PYTHONPATH
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(APPS_DIR))

import django
from django.apps import apps
from django.db import models

def clean_duplicates(items):
    """Enlève les doublons de la liste tout en préservant l'ordre."""
    clean_list = []
    for item in items:
        if item not in clean_list:
            clean_list.append(item)
    return clean_list

# (Fonctions extract_import_path, get_base_name, collect_imports, extract_router_patterns, extract_view_info, extract_urls, find_urls_in_app, find_views_in_app, find_serializers_in_app, find_forms_in_app, find_management_commands, find_signals_in_app, afficher_settings, afficher_middlewares restent inchangées)

def afficher_structure_django():
    try:
        # Configuration initiale de Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')
        django.setup()
        
        print("\n=== STRUCTURE DU PROJET DJANGO ===\n")
        print(f"📂 Chemin du projet: {BASE_DIR}")
        print(f"📂 Chemin des applications: {APPS_DIR}")
        print(f"📂 Python path: {sys.path[:2]}\n")

        # Afficher les settings
        afficher_settings()
        # Afficher les middlewares
        afficher_middlewares()

        # Vérifie d'abord les URLs principales
        main_urls = BASE_DIR / 'core' / 'urls.py'
        if main_urls.exists():
            print("\n🌐 URLs Principales:")
            urls = extract_urls(main_urls)
            for url in urls:
                print(f"  ▪️ {url}")
            # Vérifier les gestionnaires d'erreur
            try:
                main_urls_module = importlib.import_module('core.urls')
                if hasattr(main_urls_module, 'handler404'):
                    print(f"🛑 Handler 404: {main_urls_module.handler404}")
                if hasattr(main_urls_module, 'handler500'):
                    print(f"🛑 Handler 500: {main_urls_module.handler500}")
            except Exception as e:
                print(f"Erreur lors de l'importation de core.urls: {str(e)}")
            print("\n" + "-" * 50)

        # Initialiser les structures pour la représentation de la base de données
        db_models = {}

        # Parcourir toutes les applications installées
        for app_config in apps.get_app_configs():
            # Ignorer les applications Django par défaut
            if app_config.label in ['admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles']:
                continue

            print(f"\n📁 Application: {app_config.label}")
            print(f"📂 Chemin: {app_config.path}")
            print("=" * (len(app_config.label) + 13))

            try:
                # Afficher les modèles
                print("\n📊 Modèles:")
                models_found = False
                for model in app_config.get_models():
                    models_found = True
                    print(f"\n  🔹 {model.__name__}:")
                    # Ajouter le modèle à la représentation de la base de données
                    db_models[model.__name__] = {'fields': [], 'relations': []}

                    # Afficher les options Meta
                    meta_options = []
                    if model._meta.abstract:
                        meta_options.append('abstract')
                    if model._meta.db_table != model._meta.model_name:
                        meta_options.append(f"db_table='{model._meta.db_table}'")
                    if model._meta.ordering:
                        meta_options.append(f"ordering={model._meta.ordering}")
                    if meta_options:
                        print(f"     📋 Options Meta: {', '.join(meta_options)}")
                    
                    # Afficher les champs du modèle
                    fields_seen = set()
                    for field in model._meta.get_fields():
                        if field.name in fields_seen:
                            continue
                        fields_seen.add(field.name)
                        field_type = type(field).__name__
                        constraints = []
                        if hasattr(field, 'unique') and field.unique:
                            constraints.append("unique")
                        if hasattr(field, 'primary_key') and field.primary_key:
                            constraints.append("primary_key")
                        if hasattr(field, 'null') and not field.null:
                            constraints.append("required")
                        if hasattr(field, 'default') and field.default != models.fields.NOT_PROVIDED:
                            constraints.append(f"default={field.default}")
                        if hasattr(field, 'help_text') and field.help_text:
                            constraints.append(f"help_text='{field.help_text}'")
                        if hasattr(field, 'verbose_name') and field.verbose_name != field.name:
                            constraints.append(f"verbose_name='{field.verbose_name}'")
                        if hasattr(field, 'max_length') and field.max_length:
                            constraints.append(f"max_length={field.max_length}")
                        if hasattr(field, 'choices') and field.choices:
                            constraints.append(f"choices={[choice[0] for choice in field.choices]}")
                        
                        constraints_str = f" ({', '.join(constraints)})" if constraints else ""
                        
                        # Ajouter le champ au modèle dans la représentation de la base de données
                        db_models[model.__name__]['fields'].append({'name': field.name, 'type': field_type, 'constraints': constraints})

                        if isinstance(field, models.ForeignKey):
                            related_model = field.related_model.__name__
                            db_models[model.__name__]['relations'].append({'type': 'ForeignKey', 'model': related_model, 'field': field.name})
                            print(f"     ▪️ {field.name}: ForeignKey to {related_model}{constraints_str}")
                        elif isinstance(field, models.ManyToManyField):
                            related_model = field.related_model.__name__
                            db_models[model.__name__]['relations'].append({'type': 'ManyToMany', 'model': related_model, 'field': field.name})
                            print(f"     ▪️ {field.name}: ManyToManyField to {related_model}{constraints_str}")
                        elif isinstance(field, models.OneToOneField):
                            related_model = field.related_model.__name__
                            db_models[model.__name__]['relations'].append({'type': 'OneToOne', 'model': related_model, 'field': field.name})
                            print(f"     ▪️ {field.name}: OneToOneField to {related_model}{constraints_str}")
                        else:
                            print(f"     ▪️ {field.name}: {field_type}{constraints_str}")
                    
                    # Afficher les méthodes du modèle
                    methods = [method for method in dir(model) if callable(getattr(model, method)) and not method.startswith('_') and method not in ['save', 'delete', 'get_absolute_url']]
                    methods = clean_duplicates(methods)
                    if methods:
                        print("     🛠️  Méthodes:")
                        for method in methods:
                            print(f"       ▫️ {method}()")

                if not models_found:
                    print("  Aucun modèle trouvé")

                # Afficher les URLs
                app_path = Path(app_config.path)
                urls = find_urls_in_app(app_path)
                if urls:
                    print("\n🌐 URLs:")
                    for url in urls:
                        print(f"  ▪️ {url}")
                else:
                    print("\n🌐 URLs: Pas d'URLs trouvées")

                # Afficher les vues
                views = find_views_in_app(app_path)
                if views:
                    print("\n👁️  Vues:")
                    for view in views:
                        print(f"  ▪️ {view['name']}")
                        if 'methods' in view and view['methods']:
                            print(f"     📖 Méthodes: {', '.join(view['methods'])}")
                        if 'permissions' in view and view['permissions']:
                            print(f"     🔐 Permissions: {', '.join(view['permissions'])}")
                        if 'authentication' in view and view['authentication']:
                            print(f"     🛂 Authentification: {', '.join(view['authentication'])}")
                        if 'decorators' in view and view['decorators']:
                            print(f"     🎀 Décorateurs: {', '.join(view['decorators'])}")
                else:
                    print("\n👁️  Vues: Pas de vues trouvées")

                # Afficher les serializers
                serializers = find_serializers_in_app(app_path)
                if serializers:
                    print("\n📦 Serializers:")
                    for serializer in serializers:
                        print(f"  ▪️ {serializer}")
                else:
                    print("\n📦 Serializers: Pas de serializers trouvés")

                # Afficher les formulaires
                forms = find_forms_in_app(app_path)
                if forms:
                    print("\n📝 Formulaires:")
                    for form in forms:
                        print(f"  ▪️ {form}")
                else:
                    print("\n📝 Formulaires: Pas de formulaires trouvés")

                # Afficher les commandes de gestion
                commands = find_management_commands(app_path)
                if commands:
                    print("\n🛠️  Commandes de gestion personnalisées:")
                    for command in commands:
                        print(f"  ▪️ {command}")
                else:
                    print("\n🛠️  Commandes de gestion personnalisées: Pas de commandes trouvées")

                # Afficher les signaux
                signals = find_signals_in_app(app_path)
                if signals:
                    print("\n🔔 Signaux:")
                    for sig in signals:
                        print(f"  ▪️ Signal: {sig['signal']} -> Handler: {sig['handler']}")
                else:
                    print("\n🔔 Signaux: Pas de signaux trouvés")

            except Exception as e:
                print(f"\nErreur lors de l'analyse de l'application: {str(e)}")

            print("\n" + "-" * 50)

        # Afficher la représentation de la base de données
        print("\n=== REPRÉSENTATION DE LA BASE DE DONNÉES ===\n")
        for model_name, model_info in db_models.items():
            print(f"📘 Modèle: {model_name}")
            print("  📋 Champs:")
            for field in model_info['fields']:
                constraints_str = f" ({', '.join(field['constraints'])})" if field['constraints'] else ""
                print(f"     ▪️ {field['name']}: {field['type']}{constraints_str}")
            if model_info['relations']:
                print("  🔗 Relations:")
                for relation in model_info['relations']:
                    print(f"     ▫️ {relation['type']} to {relation['model']} via {relation['field']}")
            print("\n")

    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution: {str(e)}")

if __name__ == "__main__":
    afficher_structure_django()
