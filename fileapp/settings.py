"""
Django settings for fileapp project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from django.urls import reverse_lazy
import sentry_sdk
import dj_database_url
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

#   env = environ.Env(
# set casting, default value
#     DEBUG=(bool, False)
# )

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

#   environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-+cp9p6kiylf#b1v@**szdgqs(9t-_koo2y&0u@e!1%0o!47cn'm
#   CSRF_TRUSTED_ORIGINS = ['vercel.app']
CORS_ALLOW_ALL_ORIGINS: True
CORS_ORIGIN_ALLOW_ALL = True

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'authentication',
    'file',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'pwa',
    'storages',
    'redis'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fileapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fileapp.wsgi.application'
AUTH_USER_MODEL = 'authentication.CustomUser'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

#   DATABASES = {
#       'default': {
#           'ENGINE': 'django.db.backends.sqlite3',
#           'NAME': BASE_DIR / 'db.sqlite3',
#   }
#   }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': '',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASS'),
    }
}

# db_from_env = dj_database_url.config(conn_max_age=500)
# DATABASES['default'].update(db_from_env)

MISTRAL_UTIL_API_KEY = os.getenv('MISTRAL_UTIL_API_KEY')

# settings.py

# CACHES = {
#   'default': {
#        'BACKEND': 'django_redis.cache.RedisCache',
#        'LOCATION': 'redis://localhost:6379/1',  # Redis server address and database number
#        'OPTIONS': {
#            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#        }
#    }
#}

#   CACHE_TIMEOUT = 30

#   DATABASES = {
#       'default': {
#           'ENGINE': 'mssql',
#           'PORT': '1433',
#           'NAME': os.getenv("DB_NAME"),
#           'USER': os.getenv("DB_USER"),
#           'PASSWORD': os.getenv("DB_PASSWORD"),
#           'HOST': os.getenv("DB_SERVER"),
#           'OPTIONS': {
#                   'driver': 'ODBC Driver 17 for SQL Server',
#               },
#       }
#   }


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR, 'static']

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'static')
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#   DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
#   STATICFILES_STORAGE = "storages.backends.azure_storage.AzureStorage"
AZURE_ACCOUNT_NAME = os.getenv("AZURE_ACCOUNT_NAME")
AZURE_ACCOUNT_KEY = os.getenv("AZURE_ACCOUNT_KEY")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
ELASTIC_API_KEY = os.getenv('ELASTIC_API_KEY')
BREVO_API_KEY = os.getenv('BREVO_API_KEY')

PWA_APP_NAME = 'FSCL FILE PORTAL'
PWA_APP_DESCRIPTION = "Secure file portal for Clients"
PWA_APP_THEME_COLOR = '#0A0302'
PWA_APP_BACKGROUND_COLOR = '#f2f6f9'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_DEBUG_MODE = True
PWA_APP_ICONS = [
    {
        'src': 'https://fusionscl.com/wp-content/uploads/2020/04/cropped-Crop-FCSL-51-2.png',
        'sizes': '200x200'
    }
]
PWA_APP_ICONS_APPLE = [
    {
        'src': 'https://fusionscl.com/wp-content/uploads/2020/04/cropped-Crop-FCSL-51-2.png',
        'sizes': '200x200'
    }
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': 'https://fusionscl.com/wp-content/uploads/2020/04/cropped-Crop-FCSL-51-2.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'

CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')

# CELERY_BROKER_URL = 'redis://default:ZrCgGHlkv8CK5zV1WmGREQNgdMjQH9MB@redis-14782.c56.east-us.azure.redns.redis
# -cloud' '.com:14782' CELERY_RESULT_BACKEND =
# 'redis://default:ZrCgGHlkv8CK5zV1WmGREQNgdMjQH9MB@redis-14782.c56.east-us.azure.redns.redis' '-cloud.com:14782'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'

LOGIN_URL = reverse_lazy('login')

sentry_sdk.init(
    dsn="https://a6e45fc70c3d4a1f8330ffe76ded7e11@o326137.ingest.sentry.io/1833192",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

OPENAI_API_KEY = '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'
# Backblaze B2 settings
#   DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = '48efd85cc4e8'
AWS_SECRET_ACCESS_KEY = '005f24470f8569aadfdf258c807e93c48b79c35abc'
AWS_STORAGE_BUCKET_NAME = ''
AWS_S3_REGION_NAME = ''  # Leave this empty for Backblaze
AWS_S3_ENDPOINT_URL = 's3.us-east-005.backblazeb2.com'  # Replace with your endpoint URL

# Optional: Set custom domain if you've set up a CNAME record
# AWS_S3_CUSTOM_DOMAIN = 'your_custom_domain.com'

# Additional settings
AWS_DEFAULT_ACL = None  # Use bucket defaults
AWS_S3_FILE_OVERWRITE = False  # Prevent overwriting existing files
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # Cache files for 24 hours
}

MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
#   HF_TOKEN = os.getenv('HF_TOKEN')
#   HF_HUB_DISABLE_SYMLINKS_WARNING = os.getenv('HF_HUB_DISABLE_SYMLINKS_WARNING')
#   KMP_DUPLICATE_LIB_OK = os.getenv('KMP_DUPLICATE_LIB_OK')

MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024  # 10 MB
