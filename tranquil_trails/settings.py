"""
Django settings for tranquil_trails project.
"""

import importlib.util
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def env_list(name, default=""):
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


def env_str(name, default=""):
    return os.environ.get(name, default)


def get_database_config():
    database_url = env_str('DATABASE_URL').strip()
    if not database_url:
        if not DEBUG:
            raise ImproperlyConfigured(
                'DATABASE_URL must be set for production deployments.'
            )
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }

    parsed = urlparse(database_url)
    scheme = parsed.scheme.split('+', 1)[0].lower()

    if scheme in {'postgres', 'postgresql'}:
        query_params = parse_qs(parsed.query)
        sslmode = query_params.get(
            'sslmode',
            [env_str('POSTGRES_SSLMODE', 'require' if not DEBUG else 'prefer')],
        )[0]

        config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': unquote(parsed.path.lstrip('/')),
            'USER': unquote(parsed.username or ''),
            'PASSWORD': unquote(parsed.password or ''),
            'HOST': parsed.hostname or '',
            'PORT': str(parsed.port or 5432),
            'CONN_MAX_AGE': int(env_str('DATABASE_CONN_MAX_AGE', '600')),
        }
        if sslmode:
            config['OPTIONS'] = {'sslmode': sslmode}
        return config

    if scheme == 'sqlite':
        if not DEBUG:
            raise ImproperlyConfigured(
                'SQLite is only supported for local development in this project.'
            )
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': Path(unquote(parsed.path or 'db.sqlite3')),
        }

    raise ImproperlyConfigured(
        f"Unsupported DATABASE_URL scheme: {parsed.scheme!r}"
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool('DEBUG', True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env_str('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-change-me-before-deploy'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set for production deployments.')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '127.0.0.1,localhost,.onrender.com')
CSRF_TRUSTED_ORIGINS = env_list(
    'CSRF_TRUSTED_ORIGINS',
    'http://127.0.0.1:8000,http://localhost:8000,https://*.onrender.com',
)

# Application definition

HAS_WHITENOISE = importlib.util.find_spec('whitenoise') is not None

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # YOUR APPS
    'core', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if HAS_WHITENOISE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'tranquil_trails.urls'

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
                'core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'tranquil_trails.wsgi.application'

# Database
DATABASES = {
    'default': get_database_config(),
}

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = Path(env_str('DJANGO_STATIC_ROOT', BASE_DIR / 'staticfiles_build')).expanduser()
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedStaticFilesStorage'
            if HAS_WHITENOISE
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(env_str('DJANGO_MEDIA_ROOT', BASE_DIR / 'media')).expanduser()

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Razorpay Settings
RAZORPAY_KEY_ID = env_str('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = env_str('RAZORPAY_KEY_SECRET', '')

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(env_str('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', True)
    SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', True)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'

# Redirect to the 'login' path name when @login_required blocks a user
LOGIN_URL = 'login'

LOGIN_REDIRECT_URL = 'admin_dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Email Settings for Password Reset (Console Backend for testing)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
