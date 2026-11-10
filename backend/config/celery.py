import os

from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.local",
)

app = Celery("config")

# Read Celery configuration from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatically discover tasks.py in installed Django apps.
app.autodiscover_tasks()