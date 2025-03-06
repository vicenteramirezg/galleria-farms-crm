import os
import sys
from django.core.wsgi import get_wsgi_application

# Determine the project root directory (floral_crm folder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add the project root to sys.path so that "floral_crm.floral_crm" is importable.
sys.path.insert(0, PROJECT_ROOT)

# Set the default settings module to point to the nested settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.floral_crm.settings")

application = get_wsgi_application()
