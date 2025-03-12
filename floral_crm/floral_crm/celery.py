from __future__ import absolute_import, unicode_literals
import os
import django
from celery import Celery
import logging

logger = logging.getLogger(__name__)

# ✅ Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

# ✅ Initialize Django only when Celery is running
if not os.getenv("CELERY_WORKER_RUNNING"):
    django.setup()

# ✅ Initialize Celery app
app = Celery("floral_crm")

# ✅ Load settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# ✅ Explicitly discover tasks inside `crm`
app.autodiscover_tasks(["crm"])

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info(f"Debug task request: {self.request!r}")

# ✅ Log registered tasks after initialization
logger.info("Tasks autodiscovered: %s", list(app.tasks.keys()))

# Export the Celery app
__all__ = ["app"]
