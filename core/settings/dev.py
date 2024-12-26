# backend/core/settings/dev.py

from .base import *

# Activation du mode développement
DEBUG = True

# Ajoutez après DEBUG = True
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
    INTERNAL_IPS = ['127.0.0.1']
    

    
    # Configuration supplémentaire pour les fichiers statiques en développement
    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    ]
TEMPLATES[0]['DIRS'] = [
    BASE_DIR / "backend" / "templates",
    BASE_DIR / "apps" / "admin_interface" / "templates",
]
# Hôtes autorisés
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Paramètres CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Configuration des logs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# Configuration Email (console pour les tests)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache temporaire pour le développement
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
