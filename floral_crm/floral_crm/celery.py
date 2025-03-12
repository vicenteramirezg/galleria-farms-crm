from __future__ import absolute_import, unicode_literals
import os
import django
from celery import Celery
import logging

logger = logging.getLogger(__name__)

# ✅ Ensure Django settings are loaded
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

# ✅ Initialize Django before Celery runs
django.setup()

# ✅ Initialize Celery app
app = Celery("floral_crm")

# ✅ Load settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# ✅ Explicitly import crm.tasks to force Celery to register it
try:
    import crm.tasks  # 🔥 Force import
    logger.info("Successfully imported crm.tasks")
except ImportError as e:
    logger.error(f"Failed to import crm.tasks: {e}")

# ✅ Auto-discover tasks from installed apps
app.autodiscover_tasks(["crm"])

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info(f"Debug task request: {self.request!r}")

# ✅ Log registered tasks after initialization
logger.info("Tasks autodiscovered in worker: %s", list(app.tasks.keys()))

# Export the Celery app
__all__ = ["app"]
