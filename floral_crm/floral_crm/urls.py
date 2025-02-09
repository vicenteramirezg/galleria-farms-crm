from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView  # Import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('crm/', include('crm.urls')),  # Include CRM app URLs
    path('', TemplateView.as_view(template_name='crm/home.html'), name='home'),  # Root URL
    path('accounts/', include('allauth.urls'))
]