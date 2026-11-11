import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.local",
)

app = Celery("config")

# Read Celery configuration from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatically discover tasks.py in installed Django apps.
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "cleanup-quickshare-storage-every-5-minutes": {
        "task": "apps.transfers.tasks.cleanup_quickshare_storage",
        "schedule": crontab(minute="*/5"),
    },
}