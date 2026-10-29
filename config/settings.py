"""Django settings for Umusaruro.

The engine keeps datasets, their tables, and every observation read from
them in a database (SQLite by default). Uploaded files are kept under
var/, which git ignores. Configuration comes from the environment:

    DJANGO_SECRET_KEY     required unless DJANGO_DEBUG=1
    DJANGO_DEBUG          "1" for local development
    DJANGO_ALLOWED_HOSTS  comma-separated host names
    UMUSARURO_VAR         where the database and uploads live (default var/)
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("Set DJANGO_SECRET_KEY, or DJANGO_DEBUG=1 for local work.")
    SECRET_KEY = "local-development-only"

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h not in ("localhost", "127.0.0.1")]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "engine",
    "sheet",
    "farm",
]

MIDDLEWARE = [
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
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "farm.context.reader",
            ]
        },
    }
]

VAR_DIR = Path(os.environ.get("UMUSARURO_VAR", BASE_DIR / "var"))
UPLOAD_DIR = VAR_DIR / "uploads"
VAR_DIR.mkdir(parents=True, exist_ok=True)
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": VAR_DIR / "umusaruro.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
UPLOAD_MAX_BYTES = 25 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 2_621_440
FILE_UPLOAD_MAX_MEMORY_SIZE = 2_621_440
LOGIN_URL = "admin:login"

LANGUAGE_CODE = "en"
TIME_ZONE = "Africa/Kigali"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    }
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SSL_REDIRECT", "1") == "1"
    SECURE_HSTS_SECONDS = 3600
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
