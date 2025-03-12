from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

app = Celery("floral_crm")

# Load settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Use autodiscover_tasks WITHOUT arguments to find all tasks.py files
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")