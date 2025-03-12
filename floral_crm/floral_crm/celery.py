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

# Initialize Django for worker or beat processes
if "celery" in sys.argv[0]:  # Only for celery commands (worker, beat)
    from django import setup as django_setup
    django_setup()

# Autodiscover tasks
app.autodiscover_tasks(["crm"])

# Debug task
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info(f"Debug task request: {self.request!r}")

# Log registered tasks after initialization
logger.info("Tasks autodiscovered: %s", list(app.tasks.keys()))

# Export the app
__all__ = ["app"]