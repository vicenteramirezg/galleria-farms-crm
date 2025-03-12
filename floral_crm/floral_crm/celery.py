from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

app = Celery("floral_crm")

# Load settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# ✅ Force Celery to look inside the `crm` app explicitly
app.autodiscover_tasks(["crm"])  # 🔥 Explicitly list "crm"

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

# ✅ FIX: Delay the import of crm.tasks to avoid "Apps aren't loaded yet"
def celery_on_startup():
    import django
    django.setup()  # ✅ Ensure Django is fully loaded before importing tasks
    import crm.tasks  # ✅ Now import tasks safely

celery_on_startup()  # ✅ Call this function after Celery is initialized
