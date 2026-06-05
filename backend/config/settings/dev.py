"""Development settings."""

import os

from .base import *  # noqa: F401,F403

DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-only-do-not-use-in-prod")
ALLOWED_HOSTS = ["*"]

# Show emails in the console during development.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Let the Expo dev server talk to the API in development.
CORS_ALLOWED_ORIGINS += [
    "http://localhost:8081",
    "http://localhost:19006",
]
