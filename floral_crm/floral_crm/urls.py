from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView  # Import TemplateView
from crm import views
from crm.views import CustomLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('crm/', include('crm.urls')),  # Include CRM app URLs
    path('', TemplateView.as_view(template_name='crm/home.html'), name='home'),  # Root URL
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
]