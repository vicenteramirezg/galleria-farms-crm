from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

# Initialize Celery app
app = Celery("floral_crm")

# Load settings from Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks (keep this as a fallback)
app.autodiscover_tasks(["crm"])

# Explicitly import and register tasks
from crm.tasks import send_birthday_reminders, send_whatsapp_birthday_reminders
app.tasks.register(send_birthday_reminders)
app.tasks.register(send_whatsapp_birthday_reminders)

# Debug task for troubleshooting
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")