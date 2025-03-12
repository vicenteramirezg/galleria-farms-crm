from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'floral_crm.settings')

# Create the Celery app
app = Celery('floral_crm')

# Load settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# ✅ Manually import task modules to ensure Celery loads them
import crm.tasks  # 🔥 Add this line to explicitly load tasks

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')