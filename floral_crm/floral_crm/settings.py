"""
Django settings for floral_crm project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see:
https://docs.djangoproject.com/en/5.1/topics/settings/
For the full list of settings and their values, see:
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Detect if running locally or in production
IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT", "development") == "production"

# ✅ Secret Key
SECRET_KEY = os.getenv("SECRET_KEY")

# ✅ Debug Mode (Should be False in production)
DEBUG = os.getenv("DEBUG", "False") == "True"

# ✅ Allowed Hosts
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")]

# ✅ Login & Logout Redirects
LOGIN_URL = "/login/"  # Redirect users who are not logged in
LOGIN_REDIRECT_URL = "/crm/dashboard/"  # Redirect users here after logging in
LOGOUT_REDIRECT_URL = "/"  # Redirect users here after logging out

# ✅ Installed Applications
INSTALLED_APPS = [
    "django.contrib.humanize",
    "crm",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "whitenoise.runserver_nostatic",
    "django_celery_beat",
    "django_celery_results",
]

# ✅ Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

# ✅ URL Configuration
ROOT_URLCONF = "floral_crm.urls"

# ✅ Security Settings (Force HTTPS)

# ✅ Security Settings (Force HTTPS only in production)
SECURE_SSL_REDIRECT = IS_PRODUCTION  # Redirect HTTP to HTTPS in production only

if IS_PRODUCTION:
    SECURE_HSTS_SECONDS = 31536000  # Enables HTTP Strict Transport Security (HSTS)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Enable SSL behind a proxy
else:
    SECURE_HSTS_SECONDS = 0  # Disable HSTS locally
    SECURE_PROXY_SSL_HEADER = None  # Disable SSL enforcement locally

# ✅ Cookie Security
CSRF_COOKIE_SECURE = True  # Ensures CSRF cookies are only sent over HTTPS
SESSION_COOKIE_SECURE = True  # Ensures session cookies are sent over HTTPS

# ✅ CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    "https://crm.galleriafarms.com",
    "https://galleriafarms.com",
    "https://galleria-farms-crm.up.railway.app",
]

# ✅ Authentication Backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# ✅ Templates Configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "floral_crm/crm/templates",
        ],
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

# ✅ WSGI Application
WSGI_APPLICATION = "floral_crm.wsgi.application"

# ✅ Database Configuration

if IS_PRODUCTION:
    DATABASES = {
        "default": dj_database_url.config(
            default=os.getenv("DATABASE_URL"),
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ✅ Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ✅ Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ✅ Static Files Configuration
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ✅ Email Backend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# ✅ SMTP Configuration
EMAIL_HOST = os.getenv("EMAIL_HOST")  # SMTP2Go host
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))  # 2525, 587, 25 (TLS) or 465 (SSL)
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"  # Use TLS for security
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL") == "True"  # Use SSL if using port 465

# ✅ Authentication (Replace with your email credentials)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_USE_HTML = True


# ✅ Default Auto Field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ✅ Serve static files properly in development
if DEBUG:
    import mimetypes
    mimetypes.add_type("image/x-icon", ".ico", True)

CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_TASK_ALWAYS_EAGER = False
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL")
CELERY_RESULT_EXTENDED = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# Twilio settings
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # e.g., "whatsapp:+14155238886"

