from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import logging

logger = logging.getLogger(__name__)

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

# Initialize Celery app
app = Celery("floral_crm")

# Load settings from Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks
app.autodiscover_tasks(["crm"])

# Explicitly import and register tasks at module level
from crm.tasks import send_birthday_reminders, send_whatsapp_birthday_reminders
app.tasks.register(send_birthday_reminders)
app.tasks.register(send_whatsapp_birthday_reminders)
logger.info("Registered tasks at module load: %s", list(app.tasks.keys()))

# Debug task
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info(f"Debug task request: {self.request!r}")

# Export the app
__all__ = ["app"]