from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

app = Celery("floral_crm")

# Load settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# ✅ Force Celery to look inside the `crm` app explicitly
app.autodiscover_tasks(["crm"])  # 🔥 Explicitly list "crm"

# ✅ Manually import tasks from crm to ensure they are loaded
import crm.tasks  # 🔥 Ensure this is included

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
