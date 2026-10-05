"""
Django settings for agrinova project.
"""
import os
from pathlib import Path

import dj_database_url
from decouple import Csv, config

# PyMySQL shim (must run before Django DB connection)
from agrinova import pymysql_init  # noqa: F401

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config(
    'DEBUG',
    default=True,
    cast=bool
)

if os.environ.get('RENDER'):
    DEBUG = False

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv()
)



# Allow Render's automatically assigned hostname
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=Csv()
)

if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(
        f'https://{RENDER_EXTERNAL_HOSTNAME}'
    )

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'marketplace',
    'orders',
    'chatbot',
    'forecasting',
    'matching',
    'dashboard',
    'adminpanel',
    'reports',
    'cloudinary_storage',
    'cloudinary',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'agrinova.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'orders.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'agrinova.wsgi.application'

# Database configuration
#
# Local development:
# Uses the existing MySQL configuration.
#
# Render deployment:
# Uses DATABASE_URL provided by Render PostgreSQL.

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
        )
    }
else:
    DB_ENGINE = config(
        'DB_ENGINE',
        default='django.db.backends.mysql'
    )

    if 'sqlite' in DB_ENGINE:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / config(
                    'DB_NAME',
                    default='db.sqlite3'
                ),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': DB_ENGINE,
                'NAME': config(
                    'DB_NAME',
                    default='agrinova_db'
                ),
                'USER': config(
                    'DB_USER',
                    default='root'
                ),
                'PASSWORD': config(
                    'DB_PASSWORD',
                    default=''
                ),
                'HOST': config(
                    'DB_HOST',
                    default='127.0.0.1'
                ),
                'PORT': config(
                    'DB_PORT',
                    default='3306'
                ),
                'OPTIONS': {
                    'charset': 'utf8mb4',
                    'init_command': (
                        "SET sql_mode='STRICT_TRANS_TABLES'"
                    ),
                },
            }
        }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.User'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'accounts:login'

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    }
}
DEFAULT_FROM_EMAIL = 'noreply@agrinova.local'

# AI Chatbot settings
GROQ_API_KEY = config('GROQ_API_KEY', default='')
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
GEMINI_MODEL = config('GEMINI_MODEL', default='gemini-3.6-flash')
GROQ_MODEL = config('GROQ_MODEL', default='openai/gpt-oss-20b')
AI_PROVIDER_ORDER = config('AI_PROVIDER_ORDER', default='gemini,groq', cast=Csv())
CHATBOT_RATE_LIMIT = 30  # messages per hour per user
CHATBOT_RATE_WINDOW = 3600  # seconds

# RAG Knowledge Base & Vector Store settings
AGRICULTURE_KNOWLEDGE_DIR = BASE_DIR / 'agriculture_knowledge'
CHROMA_PERSIST_DIR = config('CHROMA_PERSIST_DIR', default=str(BASE_DIR / 'data' / 'chroma_db'))
RAG_TOP_K = config('RAG_TOP_K', default=4, cast=int)
RAG_RELEVANCE_THRESHOLD = config('RAG_RELEVANCE_THRESHOLD', default=0.08, cast=float)
RAG_EMBEDDING_PROVIDER = config('RAG_EMBEDDING_PROVIDER', default='local')



# Session cart key
CART_SESSION_ID = 'agrinova_cart'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('jgbe6qnt', default=''),
    'API_KEY': config('843334343498994', default=''),
    'API_SECRET': config('ugRJnoPqz_MMTymAT69uJm7LF70', default=''),
}

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}