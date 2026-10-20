"""The village: the houses' mailboxes. Ponies drop letters off over plain HTTP."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR))

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "pony-express-demo-not-a-secret")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = ["mailboxes"]

MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]

ROOT_URLCONF = "village.urls"
WSGI_APPLICATION = "village.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]

# The village's own database. The post office never sees it.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "village.sqlite3",
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=WAL;",
            "transaction_mode": "IMMEDIATE",
            "timeout": 20,
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "Europe/Berlin"
