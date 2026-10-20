"""The post office: owns the letters, posts them to the bus, reprints what goes missing."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR))

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "pony-express-demo-not-a-secret")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = ["django.contrib.staticfiles", "letters"]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "postoffice.urls"
WSGI_APPLICATION = "postoffice.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": ["django.template.context_processors.request"]
        },
    }
]

# This service's own database. The web process and the postmaster share it, so use WAL.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "postoffice.sqlite3",
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=WAL;",
            "transaction_mode": "IMMEDIATE",
            "timeout": 20,
        },
    }
}

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "Europe/Berlin"

# If a pony isn't back with a receipt after this many seconds, the letter gets reprinted.
DELIVERY_TIMEOUT = float(os.environ.get("DELIVERY_TIMEOUT", 8))

# A pony missing for longer than this is struck off the herd list. If it shows up again, it's re-adopted.
PONY_FORGET_AFTER = float(os.environ.get("PONY_FORGET_AFTER", 60))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"pika": {"level": "WARNING"}},
}
