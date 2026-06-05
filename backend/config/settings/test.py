"""Test settings: deterministic and fast."""
from .dev import *  # noqa: F401,F403

DEBUG = False

# Speed up the test suite (hashing dominates user-creation tests).
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
