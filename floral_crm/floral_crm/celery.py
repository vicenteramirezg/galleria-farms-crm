from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import logging

logger = logging.getLogger(__name__)

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

# Initialize Celery app
app = Celery("floral_crm")

# Load settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# ✅ Force Celery to auto-discover tasks from all installed Django apps
app.autodiscover_tasks()

# ✅ Explicitly import crm.tasks to ensure it's loaded
try:
    import crm.tasks  # 🔥 Force import of all tasks
    logger.info("Successfully imported crm.tasks")
except ImportError as e:
    logger.error(f"Failed to import crm.tasks: {e}")

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info(f"Debug task request: {self.request!r}")

# ✅ Log registered tasks after initialization
logger.info("Tasks autodiscovered: %s", list(app.tasks.keys()))

# Export the app
__all__ = ["app"]
