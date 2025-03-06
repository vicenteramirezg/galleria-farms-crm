import os
import sys
from django.core.wsgi import get_wsgi_application

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure the project root and Django settings module are properly set
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

application = get_wsgi_application()
