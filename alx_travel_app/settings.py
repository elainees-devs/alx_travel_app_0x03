import os
from pathlib import Path
import environ
from datetime import timedelta


# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize env
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_travel_app.settings")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-xyz123")
CHAPA_SECRET_KEY = os.getenv("CHAPA_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = [
    "alx-travel-app-0x03-z7x9.onrender.com",
    "127.0.0.1",
    "localhost",
    "testserver",
    "elainees.pythonanywhere.com",
]


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "drf_yasg",
    "django_celery_results",
    # Local
    "alx_travel_app.listings",
]
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,  # disables /accounts/login/
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": 'JWT Authorization header. Example: "Bearer {token}"',
        }
    },
}

# Rest framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


# Email settings
EMAIL_BACKEND = env("EMAIL_BACKEND").strip()
EMAIL_HOST = env("EMAIL_HOST").strip()
EMAIL_PORT = env.int("EMAIL_PORT")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER").strip()
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD").strip()
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL").strip()


# Celery settings
CELERY_BROKER_URL = "amqp://localhost"  # RabbitMQ
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Nairobi"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # add this just after SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "alx_travel_app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "alx_travel_app.wsgi.application"
# MySQL DB setup
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # default 7 days
    "ROTATE_REFRESH_TOKENS": True,  # optional
    "BLACKLIST_AFTER_ROTATION": True,  # optional
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_ALL_ORIGINS = True