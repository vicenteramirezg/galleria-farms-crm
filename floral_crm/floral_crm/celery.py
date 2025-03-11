import os
from celery import Celery

# Set default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'floral_crm.settings')

app = Celery('floral_crm')

# Load task modules from all registered Django apps
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in installed apps
app.autodiscover_tasks(lambda: [n.name for n in app.conf.installed_apps])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
