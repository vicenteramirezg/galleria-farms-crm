from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView  # Import TemplateView
from crm import views
from crm.views import CustomLogoutView
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('crm/', include('crm.urls')),  # Include CRM app URLs
    path('', TemplateView.as_view(template_name='crm/home.html'), name='home'),  # Root URL
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),  # ✅ Redirect /favicon.ico to the correct path
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])