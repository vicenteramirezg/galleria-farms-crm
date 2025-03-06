import os
import sys
from django.core.wsgi import get_wsgi_application

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add project root to Python path
sys.path.insert(0, PROJECT_ROOT)

# Set default settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

application = get_wsgi_application()
