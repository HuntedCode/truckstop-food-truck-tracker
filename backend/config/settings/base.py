"""Base settings shared across all environments.

Environment-specific settings live in dev.py, test.py, and prod.py and import
from here. See docs/architecture/tech-stack.md for the rationale.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# backend/config/settings/base.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [
        item.strip() for item in os.getenv(name, default).split(",") if item.strip()
    ]


SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "apps.core",
    "apps.accounts",
    "apps.trucks",
    "apps.appearances",
    "apps.engagement",
    "apps.notifications",
    "apps.web",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database: PostGIS. dj-database-url maps the postgis:// scheme to the
# GeoDjango backend automatically. The default targets the Docker Compose db
# service mapped to host port 5438 (so host-run manage.py works too).
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv(
            "DATABASE_URL",
            "postgis://truckstop:truckstop@localhost:5438/truckstop",
        ),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_USER_MODEL = "accounts.User"

# Web (session-auth) login flow for the owner dashboard.
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# DRF: JWT for the API/mobile, session for the HTMX web surfaces.
# Anonymous read, authenticated write (consistent with the permissions matrix
# in docs/architecture/data-model.md).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "120/min",
        "register": "10/hour",
        "events_anon": "30/min",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
}

# CORS: the API is consumed cross-origin by the Expo app. Scope to the API.
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CORS_URLS_REGEX = r"^/api/.*$"

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static / media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
# NOTE: media (`default`) is local filesystem, served publicly via /media/.
# Before collecting real verification evidence (PII), move `default` to a
# PRIVATE object store with signed URLs so /media/verifications/ is never public.
# See docs/features/owner-verification.md and cross-cutting-concerns.md.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# An appearance counts as "verified present" if its latest owner confirmation
# is within this window (see apps.appearances and docs/architecture/data-model.md).
PRESENCE_FRESHNESS_WINDOW = timedelta(hours=2)
