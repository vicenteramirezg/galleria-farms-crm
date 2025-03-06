import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "floral_crm.settings")  # ✅ Correct path

application = get_asgi_application()
