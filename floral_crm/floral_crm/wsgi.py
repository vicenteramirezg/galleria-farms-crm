import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")

application = get_wsgi_application()