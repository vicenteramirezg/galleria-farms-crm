from __future__ import absolute_import, unicode_literals
import os
import sys
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

# Only run django.setup() if this is the worker process
if "celery" in sys.argv[0]:  # Check if running as Celery worker or beat
    from django import setup as django_setup
    django_setup()
    # Explicitly import and register tasks
    from crm.tasks import send_birthday_reminders, send_whatsapp_birthday_reminders
    app.tasks.register(send_birthday_reminders)
    app.tasks.register(send_whatsapp_birthday_reminders)
    logger.info("Registered tasks in worker: %s", list(app.tasks.keys()))

# Debug task
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info(f"Debug task request: {self.request!r}")

# Export the app
__all__ = ["app"]