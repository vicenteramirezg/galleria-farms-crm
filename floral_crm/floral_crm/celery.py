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

# Debug task
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info(f"Debug task request: {self.request!r}")

# Delay task registration until Django is ready
def register_celery_tasks():
    from crm.tasks import send_birthday_reminders, send_whatsapp_birthday_reminders
    app.tasks.register(send_birthday_reminders)
    app.tasks.register(send_whatsapp_birthday_reminders)
    logger.info("Registered tasks: %s", list(app.tasks.keys()))

# Hook into Celery’s setup process
@app.on_after_configure.connect
def setup_tasks(sender, **kwargs):
    register_celery_tasks()

# Export the app
__all__ = ["app"]