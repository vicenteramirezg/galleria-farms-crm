from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf.urls import handler404
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView  # Import TemplateView
from crm import views
from crm.views import CustomLogoutView, custom_404_view
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

handler404 = custom_404_view  # Assign the custom function

urlpatterns = [
    path('admin/', admin.site.urls),
    path('install/', TemplateView.as_view(template_name='registration/install.html'), name='install'),
    path('crm/', include('crm.urls')),  # Include CRM app URLs
    path('', TemplateView.as_view(template_name='crm/home.html'), name='home'),  # Root URL
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),

    # ✅ Password Reset URLs (Corrected for HTML email rendering)
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset.html",
            email_template_name="registration/password_reset_email.html",  # ✅ Plain text fallback
            html_email_template_name="registration/password_reset_email.html",  # ✅ Ensures HTML email format
            subject_template_name="registration/password_reset_subject.txt"
        ),
        name="password_reset",
    ),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
