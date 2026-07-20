from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

LOGIN_URL = '/usuarios/login/'

# ─── SQLite para desarrollo local ───
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# SECRET_KEY para desarrollo (nunca usar en produccion)
SECRET_KEY = 'django-insecure-dev-local-key-no-usar-en-prod'
